"""
Automated testing with nox.
"""

# SPDX-License-Identifier: BSD-3-Clause

import os
import pathlib
import shutil

import nox

nox.options.default_venv_backend = "uv|venv"
nox.options.reuse_existing_virtualenvs = True

IS_CI = bool(os.getenv("CI", False))
PACKAGE_NAME = "fakepilot"

NOXFILE_PATH = pathlib.Path(__file__).parents[0]
ARTIFACT_PATHS = (
    NOXFILE_PATH / "src" / f"{PACKAGE_NAME}.egg-info",
    NOXFILE_PATH / "build",
    NOXFILE_PATH / "dist",
    NOXFILE_PATH / "__pycache__",
    NOXFILE_PATH / "src" / "__pycache__",
    NOXFILE_PATH / "src" / PACKAGE_NAME / "__pycache__",
    NOXFILE_PATH / "tests" / "__pycache__",
)


def clean(paths=ARTIFACT_PATHS):
    """
    Clean up after a test run.

    """
    # This cleanup is only useful for the working directory of a local checkout; in CI
    # we don't need it because CI environments are ephemeral anyway.
    if IS_CI:
        return
    [
        shutil.rmtree(path) if path.is_dir() else path.unlink()
        for path in paths
        if path.exists()
    ]


# Tasks which run the package's test suites.
# -----------------------------------------------------------------------------------


@nox.session(tags=["tests"])
@nox.parametrize(
    "python,bs4",
    [
        (python, bs4)
        for python in ["3.9", "3.10", "3.11", "3.12", "3.13"]
        for bs4 in ["4.12", "4.13"]
    ],
)
def tests_with_coverage(session, bs4):
    """
    Run the package's unit tests, with coverage report.
    """

    session.install(
        f"beautifulsoup4~={bs4}",
        ".[lxml]",
        "coverage",
        'tomli; python_full_version < "3.11.0a7"',
    )
    session.run(os.path.join(session.bin, "python"), "-Im", "coverage", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Wonce::DeprecationWarning",
        "-m",
        "coverage",
        "run",
        "--source",
        PACKAGE_NAME,
        "-m",
        "unittest",
        "discover",
    )
    clean()


@nox.session(python=["3.13"], tags=["tests"])
def coverage_report(session):
    """
    Combine coverage from the various test runs and output the report.
    """

    # In CI this job does not run because we substitute one that integrates with the CI
    # system.
    if IS_CI:
        session.skip(
            "Running in CI -- skipping nox coverage job in favor of CI coverage job"
        )
    session.install("coverage[toml]")
    session.run("python", "-Im", "coverage", "combine")
    session.run("python", "-Im", "coverage", "report", "--show-missing")
    session.run("python", "-Im", "coverage", "erase")


# Tasks which test the package's documentation.
# -----------------------------------------------------------------------------------


# The documentation jobs ordinarily would want to use the latest Python version, but
# currently that's 3.13 and Read The Docs doesn't yet support it. So to ensure the
# documentation jobs are as closely matched to what would happen on RTD, these jobs stay
# on 3.12 for now.
@nox.session(python=["3.12"], tags=["docs"])
def docs_build(session):
    """
    Build the package's documentation as HTML.
    """

    session.install(".", "-r", os.path.join("docs", "requirements.txt"))
    build_dir = session.create_tmp()
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "sphinx",
        "--builder",
        "html",
        "--write-all",
        "-c",
        "docs",
        "--doctree-dir",
        os.path.join(build_dir, "doctrees"),
        "docs",
        os.path.join(build_dir, "html"),
    )
    clean()


@nox.session(python=["3.12"], tags=["docs"])
def docs_docstrings(session):
    """
    Enforce the presence of docstrings on all modules, classes, functions, and
    methods.
    """

    session.install("interrogate")
    session.run(os.path.join(session.bin, "python"), "-Im", "interrogate", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "interrogate",
        "-v",
        "src",
        "tests",
        "noxfile.py",
    )
    clean()


@nox.session(python=["3.12"], tags=["docs"])
def docs_spellcheck(session):
    """
    Spell-check the package's documentation.
    """

    session.install(".", "-r", os.path.join("docs", "requirements.txt"))
    session.install("pyenchant", "sphinxcontrib-spelling")
    build_dir = session.create_tmp()
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "sphinx",
        "-W",  # Promote warnings to errors, so that misspelled words fail the build.
        "--builder",
        "spelling",
        "-c",
        "docs",
        "--doctree-dir",
        os.path.join(build_dir, "doctrees"),
        "docs",
        os.path.join(build_dir, "html"),
        # On Apple Silicon Macs, this environment variable needs to be set so
        # pyenchant can find the "enchant" C library. See
        # https://github.com/pyenchant/pyenchant/issues/265#issuecomment-1126415843
        env={"PYENCHANT_LIBRARY_PATH": os.getenv("PYENCHANT_LIBRARY_PATH", "")},
    )
    clean()


# Code formatting checks.
#
# These checks do *not* reformat code -- that happens in pre-commit hooks -- but will
# fail a CI build if they find any code that needs reformatting.
# -----------------------------------------------------------------------------------


@nox.session(python=["3.13"], tags=["formatters"])
def format_ruff(session):
    """
    Check code formatting with Ruff.
    """

    session.install("ruff")
    session.run(os.path.join(session.bin, "python"), "-Im", "ruff", "version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "ruff",
        "format",
        "--check",
        "--diff",
        "src",
        "tests",
        "docs",
        "noxfile.py",
    )
    clean()


# Linters.
# -----------------------------------------------------------------------------------


@nox.session(python=["3.13"], tags=["linters", "security"])
def lint_ruff(session):
    """
    Lint code with Ruff.
    """

    session.install("ruff")
    session.run(os.path.join(session.bin, "python"), "-Im", "ruff", "version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "ruff",
        "check",
        "--diff",
        os.path.join(".", "pyproject.toml"),
        "src",
        "tests",
    )
    clean()


@nox.session(python=["3.13"], tags=["linters", "security"])
def lint_bandit(session):
    """
    Lint code with the Bandit security analyzer.
    """

    session.install("bandit[toml]")
    session.run(os.path.join(session.bin, "python"), "-Im", "bandit", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "bandit",
        "-c",
        os.path.join(".", "pyproject.toml"),
        "-r",
        "src",
        "tests",
    )
    clean()


@nox.session(python=["3.13"], tags=["linters"])
def lint_pylint(session):
    """
    Lint code with Pylint.
    """

    session.install("pylint", ".[tests]")
    session.run(os.path.join(session.bin, "python"), "-Im", "pylint", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "pylint",
        "src",
        "tests",
    )
    clean()


# Packaging checks.
# -----------------------------------------------------------------------------------


@nox.session(python=["3.13"], tags=["packaging"])
def package_build(session):
    """
    Check that the package builds.
    """

    clean()
    session.install("build")
    session.run(os.path.join(session.bin, "python"), "-Im", "build", "--version")
    session.run(os.path.join(session.bin, "python"), "-Im", "build")


@nox.session(python=["3.13"], tags=["packaging"])
def package_description(session):
    """
    Check that the package description will render on the Python Package Index.
    """

    package_dir = session.create_tmp()
    session.install("build", "twine")
    session.run(os.path.join(session.bin, "python"), "-Im", "build", "--version")
    session.run(os.path.join(session.bin, "python"), "-Im", "twine", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "build",
        "--wheel",
        "--outdir",
        os.path.join(package_dir, "build"),
    )
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "twine",
        "check",
        os.path.join(package_dir, "build", "*"),
    )
    clean()


@nox.session(python=["3.13"], tags=["packaging"])
def package_manifest(session):
    """
    Check that the set of files in the package matches the set under version
    control.
    """

    if IS_CI:
        session.skip("check-manifest already run by earlier CI steps.")
    session.install("check-manifest")
    session.run(
        os.path.join(session.bin, "python"), "-Im", "check_manifest", "--version"
    )
    session.run(
        os.path.join(session.bin, "python"), "-Im", "check_manifest", "--verbose"
    )
    clean()


@nox.session(python=["3.13"], tags=["packaging"])
def package_pyroma(session):
    """
    Check package quality with pyroma.

    """
    session.install("pyroma")
    session.run(
        os.path.join(session.bin, "python"),
        "-c",
        'from importlib.metadata import version; print(version("pyroma"))',
    )
    session.run(os.path.join(session.bin, "python"), "-Im", "pyroma", ".")
    clean()


@nox.session(python=["3.13"], tags=["packaging"])
def package_wheel(session):
    """
    Check the built wheel package for common errors.
    """

    package_dir = session.create_tmp()
    session.install("build", "check-wheel-contents")
    session.run(os.path.join(session.bin, "python"), "-Im", "build", "--version")
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "check_wheel_contents",
        "--version",
    )
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "build",
        "--wheel",
        "--outdir",
        os.path.join(package_dir, "build"),
    )
    session.run(
        os.path.join(session.bin, "python"),
        "-Im",
        "check_wheel_contents",
        os.path.join(package_dir, "build"),
    )
    clean()
