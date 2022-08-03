# Dokter: the doctor for your Dockerfiles

The objective of `dokter` is to make your Dockerfiles better, it will make sure that your Dockerfiles:
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

`Dokter` fits into the first stage and aims to prevent building an image that exposes credentials or contains 
vulnerabilities, which at the bare minimum saves CI/CD minutes.

Separate processes like container registry scanning will also run, but they may run only after an image has been pushed,
potentially already exposing a vulnerable image to the public.


## What makes Dokter special?

Good question, `Dokter` is the byproduct of a much bigger product, 
[GitLab AI Assist](https://about.gitlab.com/handbook/engineering/incubation/ai-assist/), as a first starting point, 
Dockerfiles were chosen. A parser was developed to fully parse Dockerfiles in a format that is designed for machine 
learning. In order to train ML models, there is a need to create a large, rich dataset and in order to do that a good 
analysis of Dockerfiles is needed. Hence, the creation of `Dokter`. It will start improving your Dockerfiles from day 1
but will become much more powerful in the future, eventually it will automatically create Dockerfiles for you.


## No telemetry

No worries, your Dockerfiles remain private, `Dokter` won't share any telemetry with GitLab, perhaps at some point in 
time when machine learning models would benefit from user feedback, the option to provide anonymous feedback may be, 
with plenty of user awareness and opt-in, introduced.

## Dynamic parser  

The parser behind `Dokter` has been designed with data and ML in mind, it supports parsing of all Docker instructions 
and adds support for comments, both actual comments and commented out code. 

The parser also supports dynamic analysis, it's context aware, example:

```dockerfile
COPY . /app
```

If a static analysis was performed, it would approve the above instruction, `Dokter` however will actually list the 
files that are in `.` and analyze them against known files to contain credentials, but also filter against your 
`.dockerignore` file.

## Usage

There are a couple of ways you can use `Dokter`:

- Local
- CI/CD

It is suggested to always use both, but at least run it where you are actually building and publishing your images.

### Local usage

You will need to install `Dokter` from `pip`
```bash
pip install --upgrade dokter --extra-index-url https://gitlab.com/api/v4/projects/36078023/packages/pypi/simple
dokter -d path/to/Dockerfile
```
If you want more information you can either run it in verbose mode or ask to explain a specific rule
```bash
# Explain rule dfa001
dokter -e dfa001

# Run in verbose mode (this will be a lot of text)
dokter -v -d path/to/Dockerfile
```

You can also use docker:

```bash
docker run -it -v $(pwd):/app registry.gitlab.com/gitlab-org/incubation-engineering/ai-assist/dokter/dokter:latest dokter -d docter.Dockerfile
```

### Dockerfile formatting

`Dokter` is capable of creating a pretty formatted Dockerfile, as well as autocorrecting some errors found by the 
analyzer. It can either show `-s` or write `-w` the file, in case of writing it will overwrite the given Dockerfile, so
it's easier to review and commit changes. 

```bash
dokter -d Dockerfile -w
```

In case of showing, `Dokter` will first output the analysis report followed by the Dockerfile, at this moment it will 
output a file with some errors corrected but not all. 

```bash
dokter -d Dockerfile -s
```

You can also combine `-s` and `-w` to both show and write the Dockerfile.


### CI/CD

Usage in GitLab CI example:

```yaml
dokter:
  image: registry.gitlab.com/gitlab-org/incubation-engineering/ai-assist/dokter/dokter:latest
  stage: lint
  script:
    - dokter -d Dockerfile
```

### GitLab Code Quality

To use the output in GitLab code quality you can use below as an example:
```yaml
dokter:
  image: registry.gitlab.com/gitlab-org/incubation-engineering/ai-assist/dokter/dokter:latest
  stage: lint
  script:
    - dokter -d dokter.Dockerfile --gitlab-codequality
  artifacts:
    name: "$CI_JOB_NAME artifacts from $CI_PROJECT_NAME on $CI_COMMIT_REF_SLUG"
    expire_in: 1 day
    when: always
    reports:
      codequality:
        - "dokter-$CI_COMMIT_SHA.json"
    paths:
      - "dokter-$CI_COMMIT_SHA.json"
```

### Gotcha's

Below are some subjects that could raise questions, errors. 

#### Jinja templating

Jinja is ignored, what will happen is, the templated lines will get ignored and the Docker instructions 
will be parsed. 

Example:
```Dockerfile
FROM scratch

{% if something %} # This line will be considered empty
RUN echo "some command" # This line will be parsed
{% endif %} # This line will be considered empty
```

#### Here strings (EOF)

At this moment if you have a `here string` in your bash command, the Dockerfile will fail, it can not be parsed. Support
will be added in the future.
