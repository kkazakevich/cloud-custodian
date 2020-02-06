load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

# https://github.com/bazelbuild/rules_python
git_repository(
    name = "rules_python",
    commit = "94677401bc56ed5d756f50b441a6a5c7f735a6d4",
    remote = "https://github.com/bazelbuild/rules_python",
    shallow_since = "1573842889 -0500",
    #    sha256 = "aa96a691d3a8177f3215b14b0edc9641787abaaa30363a080165d06ab65e1161",
)

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

load("@rules_python//python:pip.bzl", "pip3_import", "pip_repositories")

pip_repositories()

pip3_import(
    name = "pip_deps",
    requirements = "//:requirements-bazel-dev.txt",
)

load("@pip_deps//:requirements.bzl", "pip_install")

pip_install()

# azure deps experimental
git_repository(
    name = "rules_python_external",
    commit = "a6f4ae984e7a5d4436fb7aed1678c117a8ddd12b",
    remote = "https://github.com/dillon-giacoppo/rules_python_external",
)

# Install the rule dependencies
load("@rules_python_external//:repositories.bzl", "rules_python_external_dependencies")
rules_python_external_dependencies()

load("@rules_python_external//:defs.bzl", azure_pip_install="pip_install")
azure_pip_install(
    name = "py_deps",
    requirements = "//tools/c7n_azure:requirements.txt",
)
