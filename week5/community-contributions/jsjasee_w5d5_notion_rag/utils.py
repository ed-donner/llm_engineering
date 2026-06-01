import re


def get_n2m_client(notion):
    """Build the shared Notion-to-Markdown client for one sync run.

    Args:
        notion: Configured `notion_client.Client` instance.

    Returns:
        Reusable `NotionToMarkdown` converter bound to the Notion client.
    """
    from notion_to_md import NotionToMarkdown

    return NotionToMarkdown(notion)


def post_process_md(md):
    """Apply light cleanup to converted markdown.

    Args:
        md: Raw markdown returned by `notion-to-md-py`.

    Returns:
        Cleaned markdown with trailing whitespace removed and long blank runs collapsed.
    """
    lines = [line.rstrip() for line in md.splitlines()]
    cleaned = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def convert_page_to_md(page_id, n2m):
    """Convert one Notion page into cleaned markdown text.

    Args:
        page_id: Notion page ID to export.
        n2m: Shared `NotionToMarkdown` client.

    Returns:
        Markdown string ready to write to disk.
    """
    md_blocks = n2m.page_to_markdown(page_id)
    raw_md = n2m.to_markdown_string(md_blocks).get("parent", "")
    return post_process_md(raw_md)
