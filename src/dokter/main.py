import argparse

from .analyzer import Analyzer


def dokter():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dockerfile", dest="dockerfile", required=False, help="Path to Dockerfile location")
    parser.add_argument("-e", "--explain", dest="explain_rule", required=False, help="Explain what a rule entails")
    parser.add_argument("-c", "--gitlab-codequality", dest="gitlab_codequality", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("-w", "--write-dockerfile", dest="write_df", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("-s", "--show-dockerfile", dest="show_df", action="store_true", required=False,
                        help="Save the output in a JSON formatted for GitLab Code Quality reports")
    parser.add_argument("-V", "--verbose", dest="verbose", required=False, action="store_true",
                        help="Verbose information")
    args = parser.parse_args()
    a = Analyzer(**vars(args))
    if args.explain_rule is None:
        warnings, errors = a.run()
        if errors > 0:
            exit(1)


if __name__ == "__main__":
    dokter()
