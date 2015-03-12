import os

import sublime
from sublime_plugin import WindowCommand, TextCommand, EventListener

from ..git_command import GitCommand
from ...common import util

VIEW_TITLE = "TAGS: {}"

LOCAL_TEMPLATE = """
  LOCAL:
{}
"""

VIEW_HEADER_TEMPLATE = """
  BRANCH:  {branch_status}
  ROOT:    {repo_root}
  HEAD:    {current_head}
"""

NO_TAGS_MESSAGE = """
  Your repository has no tags.
"""

KEY_BINDINGS_MENU = """
  #############
  ## ACTIONS ##
  #############

  [c] create (NYI)
  [d] delete (NYI)
  [D] delete locally and remotely (NYI)
  [p] push to remote(s) (NYI)
  [P] push all tags to remote(s) (NYI)
  [l] view commit diff (NYI)

  ###########
  ## OTHER ##
  ###########

  [r] refresh status

-
"""

view_section_ranges = {}


class GsShowTagsCommand(WindowCommand, GitCommand):

    """
    Open a tags view for the active git repository.
    """

    def run(self):
        repo_path = self.repo_path
        title = VIEW_TITLE.format(os.path.basename(repo_path))
        tags_view = util.view.get_read_only_view(self, "tags")
        util.view.disable_other_plugins(tags_view)
        tags_view.set_name(title)
        tags_view.set_syntax_file("Packages/GitSavvy/syntax/tags.tmLanguage")
        tags_view.settings().set("git_savvy.repo_path", repo_path)
        tags_view.settings().set("word_wrap", False)
        self.window.focus_view(tags_view)
        tags_view.sel().clear()

        tags_view.run_command("gs_tags_refresh")


class GsTagsRefreshCommand(TextCommand, GitCommand):

    """
    Get the current state of the git repo and display tags and command
    menu to the user.
    """

    def run(self, edit, **kwargs):
        sublime.set_timeout_async(lambda: self.run_async(**kwargs))

    def run_async(self):
        view_contents, ranges = self.get_contents()
        view_section_ranges[self.view.id()] = ranges
        self.view.run_command("gs_replace_view_text", {"text": view_contents})

    def get_contents(self):
        """
        Build string to use as contents of tags view. Includes repository
        information in the header, per-tag information, and a key-bindings
        menu at the bottom.
        """
        header = VIEW_HEADER_TEMPLATE.format(
            branch_status=self.get_branch_status(),
            repo_root=self.repo_path,
            current_head=self.get_latest_commit_msg_for_head()
        )

        cursor = len(header)
        local = self.get_tags()
        local_region = (sublime.Region(0, 0), ) * 1

        def get_region(new_text):
            nonlocal cursor
            start = cursor
            cursor += len(new_text)
            end = cursor
            return sublime.Region(start, end)

        view_text = ""

        if local:
            local_lines = "\n".join(
                "    {} {}".format(t.sha[:7], t.tag)
                for t in local
                )
            local_text = LOCAL_TEMPLATE.format(local_lines)
            local_region = get_region(local_text)
            view_text += local_text

        view_text = view_text or NO_TAGS_MESSAGE

        contents = header + view_text + KEY_BINDINGS_MENU

        return contents, (local_region)


class GsTagsFocusEventListener(EventListener):

    """
    If the current view is a tags view, refresh the view with
    the repository's tags when the view regains focus.
    """

    def on_activated(self, view):
        if view.settings().get("git_savvy.tags_view") == True:
            view.run_command("gs_tags_refresh")

