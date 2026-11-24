from uuid import NAMESPACE_URL, uuid5


def demo_id(workspace: str, kind: str, slug: str):
    return uuid5(NAMESPACE_URL, f"spoke/{workspace}/{kind}/{slug}")
