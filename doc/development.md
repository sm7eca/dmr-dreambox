
# Development

## Generate Ctags

## Github Workflow

- create an issue
- assign an this issue to you
- do not forget to pull the latest changes
- create a new branch
- develop the code changes
- test code changes
- write a good commit message in English, make use of "closes #<ISSUE-ID>" in the commit message
- push the changes to Github
- Goto [Pull Request page at Github](https://github.com/sm7eca/dmr-dreambox/pulls)
- Click on the button "Create new pull request"
- Assign the Pull Request to another collaborator if applicable
- Wait for the code review results
- Review will merge the Pull Request.
- Done!

## Prepare HW

### Nextion Display

- format a micro SD card on a Windows 10 system
- copy the file with file extension "tft" to the SD card
- power off the Nextion display
- insert the SD card
- power up the Nextion display
- wait until the process is finished with a SUCCESS message
- remove power, remove SD card
- restart the DMR hardware

## Release Process

- Ensure that you have updated the version string in [sketch_dreambox.ino](sketch_dreambox/sketch_dreambox.ino)
- Ensure that you do not have any local code changes
- Run the following Makefile target

```Shell
make release
```

- Go to [DMR Dreambox - Release Page](https://github.com/sm7eca/dmr-dreambox/releases)
- Press on "Draft a new release"
- Reuse the release name/tag
- Attach both ZIP file as well as sha256sum file to the release
- Done!

# References

* [How to write a good commit message](https://chris.beams.io/posts/git-commit/)
* [Nextion protocol specification](https://nextion.tech/instruction-set/)
