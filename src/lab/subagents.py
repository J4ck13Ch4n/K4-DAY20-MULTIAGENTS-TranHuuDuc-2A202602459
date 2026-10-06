"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when you need to understand the task before changing anything: "
                "delegate to explorer to read instruction.md, docstrings, config and sample data, "
                "then return a factual summary of requirements, file paths and edge cases."
            ),
            "system_prompt": (
                "You are an explorer subagent. Read the files listed in the delegation message "
                "(instruction, docstrings, configs, sample data) and report facts only: "
                "requirements, relevant file paths, data formats and edge cases. "
                "Do not modify any file."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when the plan is clear and files need to be created or edited and verified: "
                "delegate to implementer with the full task rules and file paths, "
                "and ask it to apply the change, run tests or scripts, and report what changed."
            ),
            "system_prompt": (
                "You are an implementer subagent. Apply exactly the change described in the delegation "
                "message, run the relevant tests or scripts to verify, and report the files changed "
                "and the verification output. Do not skip verification."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use after a change is done and you need an independent check before finishing: "
                "delegate to reviewer with the task rules and the list of changed files, "
                "and ask it to verify the result against the requirements and edge cases without modifying files."
            ),
            "system_prompt": (
                "You are a reviewer subagent. Independently check the files listed in the delegation "
                "message against the task rules and edge cases, compare outputs with requirements, "
                "and report pass or fail per rule with evidence. Do not modify any file."
            ),
        },
    ]
