# Dockter: the doctor for your Dockerfiles

The objective of Dockter is to make your Dockerfiles better, it will make sure that your Dockerfiles:
- build secure images
- build smaller images
- build faster
- follow best practices
- are pretty formatted

## DevOps lifecycle

Typically, a CI/CD pipeline consists of roughly the following steps:
- lint code
- build Docker image
- run tests in Docker image
- scan image for vulnerabilities (hopefully)
- push image to registry
- deploy image

`Dockter` fits into the first stage and aims to prevent building an image that exposes credentials or contains 
vulnerabilities, which at the bare minimum saves CI/CD minutes.

Separate processes like container registry scanning will also run, but they may run only after an image has been pushed,
potentially already exposing a vulnerable image to the public.


## What makes Dockter special?

Good question, `Dockter` is the byproduct of a much bigger product, 
[GitLab AI Assist](https://about.gitlab.com/handbook/engineering/incubation/ai-assist/), as a first starting point, 
Dockerfiles were chosen. A parser was developed to fully parse Dockerfiles in a format that is designed for machine 
learning. In order to train ML models, there is a need to create a large, rich dataset and in order to do that a good 
analysis of Dockerfiles is needed. Hence, the creation of `Dockter`. It will start improving your Dockerfiles from day 1
but will become much more powerful in the future, eventually it will automatically create Dockerfiles for you.


## No telemetry

No worries, your Dockerfiles remain private, `Dockter` won't share any telemetry with GitLab, perhaps at some point in 
time when machine learning models would benefit from user feedback, the option to provide anonymous feedback may be, 
with plenty of user awareness and opt-in, introduced.

## Dynamic parser  

The parser behind `Dockter` has been designed with data and ML in mind, it supports parsing of all Docker instructions 
and adds support for comments, both actual comments and commented out code. 

The parser also supports dynamic analysis, it's context aware, example:

```dockerfile
COPY . /app
```

If a static analysis was performed, it would approve the above instruction, `Dockter` however will actually list the 
files that are in `.` and analyze them against known files to contain credentials, but also filter against your 
`.dockerignore` file.

## Usage

There are a couple of ways you can use `Dockter`:

- Local
- CI/CD

It is suggested to always use both, but at least run it where you are actually building and publishing your images.

### Local usage

You will need to install `Dockter` from `pip`
```bash
pip install --upgrade dockter --extra-index-url https://gitlab.com/api/v4/projects/36078023/packages/pypi/simple
dockter -d path/to/Dockerfile
```
If you want more information you can either run it in verbose mode or ask to explain a specific rule
```bash
# Explain rule dfa001
docker -e dfa001

# Run in verbose mode (this will be a lot of text)
dockter -v -d path/to/Dockerfile
```

You can also use docker:

```bash
docker run -it -v $(pwd):/app registry.gitlab.com/gitlab-org/incubation-engineering/ai-assist/dockter/dockter:latest dockter -d docter.Dockerfile
```

### CI/CD

Usage in GitLab CI example:

```yaml
dockter:
  image: registry.gitlab.com/gitlab-org/incubation-engineering/ai-assist/dockter/dockter:latest
  stage: lint
  script:
    - dockter -d Dockerfile
```
