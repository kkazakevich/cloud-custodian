load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")

FILE_HASH_SCRIPT_NAME = "file_hash.py"

def _impl_a(ctx):
    inputs = ctx.attr.whl_file.data_runfiles.files.to_list()
    print(ctx.workspace_name)
    python_script_file = False
    for f in ctx.attr._add_ep_runner.data_runfiles.files.to_list():
        if f.basename == FILE_HASH_SCRIPT_NAME:
            python_script_file = f
            break
    if not python_script_file:
        fail("Can't find 'file_hash.py' in data of the run-add-ep-script rule")
    inputs.append(python_script_file)

    # print("kek")
    out_file = ctx.outputs.output
    contents = []
    args = ctx.actions.args()
    for k, v in ctx.attr.entry_points.items():
        contents.append("[%s]" % k)
        for p in v:
            contents.append(p)

    #    print(ctx.attr.setup.txt1, "KEK")

    #    ctx.actions.run(
    #        inputs = inputs,
    #        outputs = [out_file],
    #        executable = ,
    #        progress_message = "Building wheel",
    #    )
    contents = "\\n".join(contents)
    ctx.actions.run(
        inputs = inputs,
        outputs = [out_file],
        arguments = [ctx.attr.distr_info, inputs[0].path, contents, out_file.path],
        executable = ctx.executable._add_ep_runner,
        progress_message = "Building wheel",
    )

_add_entry_points = rule(
    implementation = _impl_a,
    attrs = {
        "entry_points": attr.string_list_dict(mandatory = True),
        "distr_info": attr.string(mandatory = True),
        "whl_file": attr.label(mandatory = True),
        "output": attr.output(doc = "The generated file"),
        "_add_ep_runner": attr.label(
            executable = True,
            cfg = "host",
            default = ":run-add-ep-script",
        ),
        #        "setup": attr.label(
        #            cfg = "host",
        #            executable = False,
        #            default = ":run-add-ep-script",
        #        ),
    },
)

def define_add_ep_rule():
    native.sh_binary(
        name = "run-add-ep-script",
        srcs = ["add-entry-points-to-wheel.sh"],
        data = ["file_hash.py"],
    )

def define_path_to_setup_rule(py_wheel_rule_name):
    native.sh_binary(
        name = py_wheel_rule_name + "sh",
        srcs = ["setup.py"],
        data = ["setup.py"],
    )

def _impl_wheel(ctx):
    for f in ctx.attr.setup.data_runfiles.files.to_list():
        if f.is_source:
            input = f
            print(dir(input))
            #            new_runner = ctx.actions.declare_file(f.basename + "output_artefact")

        else:
            fail("kek")

        return struct(txt1 = "55")

_py_wheel = rule(
    implementation = _impl_wheel,
    attrs = {
        "setup": attr.label(
            cfg = "host",
            executable = True,
            default = ":run-add-ep-script",
        ),
    },
)

def get_version(name):
    return _py_wheel(
        name = name + "1",
        setup = name + "sh",
    )

def py_wheel_with_custom_version(py_wheel_rule_name, version, **kwargs):
    py_wheel(
        name = py_wheel_rule_name,
        distribution = kwargs["distribution"],
        strip_path_prefixes = kwargs["strip_path_prefixes"],
        version = version,
        deps = kwargs["deps"],
    )

def py_wheel_entry_points_ext(**kwargs):
    if kwargs.get("entry_points"):
        entry_points = kwargs.pop("entry_points")
    else:
        fail("Entry points not specified")
    py_wheel_rule_name = kwargs["name"] + "_wheel"
    kwargs.pop("version")
    version = "55"
    print(_py_wheel(name = py_wheel_rule_name + "ss"))
    print(get_version(py_wheel_rule_name))
    py_wheel_with_custom_version(py_wheel_rule_name, version, **kwargs)
    define_add_ep_rule()
    define_path_to_setup_rule(py_wheel_rule_name)
    outfile = "out/" + "-".join(
        [
            kwargs["distribution"],
            version,
            "py3",
            "none",
            "any",
        ],
    ) + ".whl"
    _add_entry_points(
        name = kwargs["name"],
        entry_points = entry_points,
        distr_info = kwargs["distribution"] + "-" + version,
        whl_file = "//:" + py_wheel_rule_name,
        output = outfile,
        #        setup = "//:" + py_wheel_rule_name + "1",
    )
