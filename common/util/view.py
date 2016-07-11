import bisect

import sublime


##############
# DECORATORS #
##############

def single_cursor_pt(run):
    def decorated_run(self, *args, **kwargs):
        view = self.view if hasattr(self, "view") else self.window.active_view()
        cursors = view.sel()
        if not cursors:
            return

        return run(self, cursors[0].a, *args, **kwargs)
    return decorated_run


def single_cursor_coords(run):
    def decorated_run(self, *args, **kwargs):
        view = self.view if hasattr(self, "view") else self.window.active_view()
        cursors = view.sel()
        if not cursors:
            return
        coords = view.rowcol(cursors[0].a)

        return run(self, coords, *args, **kwargs)

    return decorated_run


#############################
# NEW-VIEW HELPER FUNCTIONS #
#############################

def get_scratch_view(context, name, read_only=True):
    """
    Create and return a read-only view.
    """
    view = new_file(context)
    view.settings().set("git_savvy.{}_view".format(name), True)
    view.set_scratch(True)
    view.set_read_only(read_only)
    return view


def _focus_other_group(context):
    """
    Set focus to other group, if open_views_in_other_group settings is true.
    """
    window = context.window if hasattr(context, "window") else context.view.window()
    savvy_settings = sublime.load_settings("GitSavvy.sublime-settings")
    in_other = savvy_settings.get("open_views_in_other_group")
    num_groups = window.num_groups()
    group = 0
    if (num_groups > 1) and in_other:
        if hasattr(context, 'view'):
            (group, index) = window.get_view_index(context.view)
        else:
            group = window.active_group()
        group = (group + 1) % num_groups
    window.focus_group(group)


def new_file(context):
    """
    Open a file and return the view. Opens in other group if multiple groups
    exist.
    """
    window = context.window if hasattr(context, "window") else context.view.window()
    _focus_other_group(context)
    return window.new_file()


def open_file(context, path):
    """
    Open a file and return the view. Opens in other group if multiple groups
    exist.
    """
    window = context.window if hasattr(context, "window") else context.view.window()
    _focus_other_group(context)
    return window.open_file(path)


def get_is_view_of_type(view, typ):
    """
    Determine if view is of specified type.
    """
    return not not view.settings().get("git_savvy.{}_view".format(typ))


##########
# GLOBAL #
##########

def refresh_gitsavvy(view):
    """
    Called after GitSavvy action was taken that may have effected the
    state of the Git repo.
    """
    if view.settings().get("git_savvy.interface") is not None:
        view.run_command("gs_interface_refresh")
    if view.settings().get("git_savvy.branch_commit_history_view") is not None:
        view.run_command("gs_branches_diff_commit_history_refresh")

    view.run_command("gs_update_status_bar")


def handle_closed_view(view):
    if view.settings().get("git_savvy.interface") is not None:
        view.run_command("gs_interface_close")
    if view.settings().get("git_savvy.edit_view"):
        view.run_command("gs_edit_view_close")
    if view.settings().get("git_savvy.commit_view"):
        view.run_command("gs_commit_view_close")


############################
# IN-VIEW HELPER FUNCTIONS #
############################

def move_cursor(view, line_no, char_no):
    # Line numbers are one-based, rows are zero-based.
    line_no -= 1

    # Negative line index counts backwards from the last line.
    if line_no < 0:
        last_line, _ = view.rowcol(view.size())
        line_no = last_line + line_no + 1

    pt = view.text_point(line_no, char_no)
    view.sel().clear()
    view.sel().add(sublime.Region(pt))
    view.show(pt)


def _region_within_regions(all_outer, inner):
    for outer in all_outer:
        if outer.begin() <= inner.begin() and outer.end() >= inner.end():
            return True
    return False


def get_lines_from_regions(view, regions, valid_ranges=None):
    if valid_ranges == []:
        return []

    line_regions = (view.line(region) for region in regions)

    valid_regions = ([region for region in line_regions if _region_within_regions(valid_ranges, region)]
                     if valid_ranges else
                     line_regions)

    return [line for region in valid_regions for line in view.substr(region).split("\n")]


def get_instance_before_pt(view, pt, pattern):
    instances = tuple(region.a for region in view.find_all(pattern))
    instance_index = bisect.bisect(instances, pt) - 1
    return instances[instance_index] if instance_index >= 0 else None


def get_instance_after_pt(view, pt, pattern):
    instances = tuple(region.a for region in view.find_all(pattern))
    instance_index = bisect.bisect(instances, pt)
    return instances[instance_index] if instance_index < len(instances) else None


#################
# MISCELLANEOUS #
#################

def disable_other_plugins(view):
    # Disable key-bindings for Vitageous
    # https://github.com/guillermooo/Vintageous/wiki/Disabling
    if sublime.load_settings("GitSavvy.sublime-settings").get("vintageous_friendly", False) is False:
        view.settings().set("__vi_external_disable", False)
