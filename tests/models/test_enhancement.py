from docsible.models.enhancement import Difficulty, Enhancement


class TestDifficulty:
    def test_quick_value(self):
        assert Difficulty.QUICK.value == "quick"

    def test_medium_value(self):
        assert Difficulty.MEDIUM.value == "medium"

    def test_advanced_value(self):
        assert Difficulty.ADVANCED.value == "advanced"

    def test_difficulty_title_quick(self):
        assert Difficulty.QUICK.value.title() == "Quick"

    def test_difficulty_title_medium(self):
        assert Difficulty.MEDIUM.value.title() == "Medium"

    def test_difficulty_title_advanced(self):
        assert Difficulty.ADVANCED.value.title() == "Advanced"

    def test_all_three_members_exist(self):
        members = {d.value for d in Difficulty}
        assert members == {"quick", "medium", "advanced"}


class TestEnhancementCreation:
    def test_basic_creation(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert enh.action == "Add examples/"
        assert enh.value == "to help users get started"
        assert enh.difficulty == Difficulty.QUICK
        assert enh.time_estimate == "5 min"

    def test_default_priority_is_one(self):
        enh = Enhancement(
            action="Add something",
            value="for better quality",
            difficulty=Difficulty.MEDIUM,
            time_estimate="10 min",
        )
        assert enh.priority == 1

    def test_optional_command_defaults_to_none(self):
        enh = Enhancement(
            action="Do something",
            value="for clarity",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert enh.command is None

    def test_optional_learn_more_url_defaults_to_none(self):
        enh = Enhancement(
            action="Do something",
            value="for clarity",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert enh.learn_more_url is None

    def test_custom_priority(self):
        enh = Enhancement(
            action="Do something",
            value="for something",
            difficulty=Difficulty.ADVANCED,
            time_estimate="1 hour",
            priority=3,
        )
        assert enh.priority == 3

    def test_with_command(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            command="mkdir -p examples",
        )
        assert enh.command == "mkdir -p examples"

    def test_with_learn_more_url(self):
        enh = Enhancement(
            action="Add meta/main.yml",
            value="for Galaxy publishing",
            difficulty=Difficulty.QUICK,
            time_estimate="10 min",
            learn_more_url="https://docs.ansible.com/ansible/latest/galaxy/user_guide.html",
        )
        assert enh.learn_more_url == "https://docs.ansible.com/ansible/latest/galaxy/user_guide.html"

    def test_all_difficulties_accepted(self):
        for diff in Difficulty:
            enh = Enhancement(
                action="Some action",
                value="some value",
                difficulty=diff,
                time_estimate="5 min",
            )
            assert enh.difficulty == diff


class TestEnhancementFormattedMessage:
    def test_formatted_message_without_command_contains_action(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert "Add examples/" in enh.formatted_message

    def test_formatted_message_without_command_contains_value(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert "to help users get started" in enh.formatted_message

    def test_formatted_message_without_command_contains_difficulty_title(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert "Quick" in enh.formatted_message

    def test_formatted_message_without_command_contains_time_estimate(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert "5 min" in enh.formatted_message

    def test_formatted_message_without_command_has_no_run_arrow(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
        )
        assert "→ Run:" not in enh.formatted_message

    def test_formatted_message_with_command_contains_run_arrow(self):
        enh = Enhancement(
            action="Add examples/",
            value="to help users get started",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            command="mkdir -p examples",
        )
        assert "→ Run: mkdir -p examples" in enh.formatted_message

    def test_formatted_message_medium_difficulty_parenthetical(self):
        enh = Enhancement(
            action="Document variables",
            value="for clarity",
            difficulty=Difficulty.MEDIUM,
            time_estimate="20 min",
        )
        assert "(Medium: 20 min)" in enh.formatted_message

    def test_formatted_message_advanced_difficulty_parenthetical(self):
        enh = Enhancement(
            action="Refactor tasks",
            value="for reusability",
            difficulty=Difficulty.ADVANCED,
            time_estimate="1 hour",
        )
        assert "(Advanced: 1 hour)" in enh.formatted_message

    def test_formatted_message_format_structure(self):
        enh = Enhancement(
            action="Add meta/main.yml",
            value="for Galaxy publishing and dependencies",
            difficulty=Difficulty.QUICK,
            time_estimate="10 min",
        )
        msg = enh.formatted_message
        # Format: "action value (Difficulty: time)"
        assert msg.startswith("Add meta/main.yml for Galaxy publishing")
        assert "(Quick: 10 min)" in msg

    def test_formatted_message_command_on_new_line(self):
        enh = Enhancement(
            action="Run lint",
            value="to catch issues",
            difficulty=Difficulty.QUICK,
            time_estimate="2 min",
            command="ansible-lint .",
        )
        msg = enh.formatted_message
        lines = msg.split("\n")
        assert len(lines) == 2
        assert "→ Run: ansible-lint ." in lines[1]
