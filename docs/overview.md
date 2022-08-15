| Rule name   | Short description                                                                                               | More information    |
|:------------|:----------------------------------------------------------------------------------------------------------------|:--------------------|
| dfa000      | Violation of Shellcheck rule                                                                                    | [dfa000](dfa000.md) |
| dfa001      | Verify that no credentials are leaking by copying in sensitive files.                                           | [dfa001](dfa001.md) |
| dfa002      | Use a .dockerignore file to exclude files being copied over.                                                    | [dfa002](dfa002.md) |
| dfa003      | When using "COPY . <target>" make sure to have a .dockerignore file. Best to copy specific folders.             | [dfa003](dfa003.md) |
| dfa004      | Verify that build args doesn't contain sensitive information, use secret mounts instead.                        | [dfa004](dfa004.md) |
| dfa005      | Don't use root but use the least privileged user.                                                               | [dfa005](dfa005.md) |
| dfa006      | The name of the Dockerfile must be 'Dockerfile' or a pattern of '<purpose>.Dockerfile'                          | [dfa006](dfa006.md) |
| dfa007      | Only use ADD for downloading from a URL or automatically unzipping local files, use COPY for other local files. | [dfa007](dfa007.md) |
| dfa008      | Chain multiple RUN instructions together to reduce the number of layers and size of the image.                  | [dfa008](dfa008.md) |
| dfa009      | To be added: Follow correct order to optimize caching.                                                          | [dfa009](dfa009.md) |
| dfa010      | Include a healthcheck for long-running or persistent containers.                                                | [dfa010](dfa010.md) |
| dfa011      | CMD or ENTRYPOINT should be the last instruction.                                                               | [dfa011](dfa011.md) |
| dfa012      | MAINTAINER is deprecated, use LABEL instead.                                                                    | [dfa012](dfa012.md) |