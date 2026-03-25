"""Confluence Data Center API client for publishing roadmaps."""

from __future__ import annotations

import httpx


class ConfluenceError(Exception):
    """Raised when a Confluence API call fails."""


class ConfluenceClient:
    """Thin client for the Confluence Server/DC REST API."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _raise(self, response: httpx.Response) -> None:
        if not response.is_success:
            try:
                msg = response.json().get("message", response.text)
            except Exception:
                msg = response.text
            raise ConfluenceError(f"HTTP {response.status_code}: {msg}")

    def find_page(self, space_key: str, title: str) -> dict[str, object] | None:
        """Return the page dict if *title* exists in *space_key*, else None."""
        response = self._client.get(
            self._url("/rest/api/content"),
            params={"spaceKey": space_key, "title": title, "expand": "version"},
        )
        self._raise(response)
        results: list[dict[str, object]] = response.json().get("results", [])
        return results[0] if results else None

    def find_parent_page(self, space_key: str, title: str) -> str:
        """Return the page ID for *title* in *space_key*, raising if not found."""
        page = self.find_page(space_key, title)
        if page is None:
            raise ConfluenceError(
                f"Parent page '{title}' not found in space '{space_key}'"
            )
        return str(page["id"])

    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
    ) -> dict[str, object]:
        """Create a new page and return the full page dict."""
        payload: dict[str, object] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        response = self._client.post(self._url("/rest/api/content"), json=payload)
        self._raise(response)
        return response.json()  # type: ignore[no-any-return]

    def update_page(
        self, page_id: str, title: str, body: str, current_version: int
    ) -> dict[str, object]:
        """Update an existing page to a new body."""
        payload: dict[str, object] = {
            "type": "page",
            "title": title,
            "version": {"number": current_version + 1},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        response = self._client.put(
            self._url(f"/rest/api/content/{page_id}"), json=payload
        )
        self._raise(response)
        return response.json()  # type: ignore[no-any-return]

    def publish(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_title: str | None = None,
    ) -> str:
        """Publish *body* (Confluence storage format) and return the page web URL.

        Creates the page if it doesn't exist; updates it if it does.
        """
        page = self.find_page(space_key, title)

        if page is None:
            parent_id: str | None = None
            if parent_title:
                parent_id = self.find_parent_page(space_key, parent_title)
            page = self.create_page(space_key, title, body, parent_id=parent_id)
        else:
            version = int(page["version"]["number"])  # type: ignore[index]
            page = self.update_page(str(page["id"]), title, body, version)

        page_id = str(page["id"])
        links: dict[str, str] = page.get("_links", {})  # type: ignore[assignment]
        webui = links.get("webui", f"/pages/viewpage.action?pageId={page_id}")
        base = links.get("base", self._base)
        return f"{base}{webui}"
