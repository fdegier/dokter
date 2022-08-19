import argparse

from . import __version__
from .analyzer import Analyzer


def dokter():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dockerfile", dest="dockerfile", required=False, help="Path to Dockerfile location")
    parser.add_argument("-e", "--explain", dest="explain_rule", required=False, help="Explain what a rule entails")
    parser.add_argument("-c", "--gitlab-codequality", dest="gitlab_codequality", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("--sast", dest="gitlab_sast", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab SAST reports")
    parser.add_argument("-w", "--write-dockerfile", dest="write_df", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("-s", "--show-dockerfile", dest="show_df", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("-V", "--verbose", dest="verbose", required=False, action="store_true",
                        help="Verbose information")
    parser.add_argument("--dockerignore", dest="dockerignore", required=False, default=".dockerignore",
                        help="Path to dockerignore file, default: .dockerignore")
    parser.add_argument("-v", "--version", dest="version", required=False, action="store_true",
                        help="Print version of Dokter")
    args = parser.parse_args()
    if args.version is True:
        print(__version__)
        exit(0)

    a = Analyzer(**vars(args))
    if args.explain_rule is None:
        result = a.run()
        del result["INFO"]
        if sum(result.values()) > 0:
            exit(1)


if __name__ == "__main__":
    dokter()
