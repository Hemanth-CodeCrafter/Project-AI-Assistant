def execute_on_mobile(action, query=None):
    print(f"[MOBILE] {action} | {query}")
    return f"Sent '{action}' to mobile."


def execute_on_tv(action, query=None):
    print(f"[TV] {action} | {query}")
    return f"Sent '{action}' to TV."