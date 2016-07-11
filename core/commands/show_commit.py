from sublime_plugin import WindowCommand, TextCommand

from ..git_command import GitCommand
from ...common import util


SHOW_COMMIT_TITLE = "COMMIT: {}"


class GsShowCommitCommand(WindowCommand, GitCommand):

    def run(self, commit_hash):
        repo_path = self.repo_path
        view = util.view.get_scratch_view(self, 'show_commit')
        view.set_syntax_file("Packages/GitSavvy/syntax/show_commit.sublime-syntax")
        view.settings().set("git_savvy.show_commit_view.commit", commit_hash)
        view.settings().set("git_savvy.repo_path", repo_path)
        view.settings().set("word_wrap", False)
        view.settings().set("line_numbers", False)
        view.set_name(SHOW_COMMIT_TITLE.format(commit_hash[:7]))
        view.run_command("gs_show_commit_initialize_view")


class GsShowCommitInitializeView(TextCommand, GitCommand):

    def run(self, edit):
        commit_hash = self.view.settings().get("git_savvy.show_commit_view.commit")
        content = self.git("show", "--no-color", commit_hash)
        self.view.run_command("gs_replace_view_text", {"text": content, "nuke_cursors": True})
        self.view.set_read_only(True)
