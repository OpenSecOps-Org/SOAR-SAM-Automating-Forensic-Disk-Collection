# Change Log

## v1.2.6
    * Updated GitHub remote references in publish.zsh script to use only OpenSecOps-Org, removed Delegat-AB
    * Updated default artifact bucket name from 'delegat-soar-forensic-artifacts' to 'OpenSecOps-soar-forensic-artifacts'

## v1.2.5
    * Updated GitHub organization name from CloudSecOps-Org to OpenSecOps-Org.
    * Updated references to CloudSecOps-Installer to Installer.

## v1.2.4
    * File paths corrected for the new name of the installer.

## v1.2.3
    * Updated LICENSE file to MPL 2.0.

## v1.2.2
    * Updated publish.zsh to support dual-remote publishing to CloudSecOps-Org repositories.

## v1.2.1
    * Python v3.12.2.
    * `.python-version` file to support `pyenv`.

## v1.2.0
    * Parametrised the instance types used in diskForensicImageBuilder.

## v1.1.4
    * Parametrised the instance type used during forensics operations.
      (The instance types used during production of the AMI remain to be done.)

## v1.1.3
    * Trying to run an m5a.large (hardcoded!) isn't a good idea as it doesn't exist
      in all regions. Replaced it with "m5.large" for now, will parametrise it as
      the next step.

## v1.1.2
    * Corrected alarm logical name.

## v1.1.1
    * Added SOAR monitoring of the state machine.

## v1.1.0
    * ForensicsAMI is now ForensicsAMIs and a map.

## v1.0.2
    * Bucket names now include account number and region.

## v1.0.1
    * Open-source credits and URLs
    * Fixed installer initial stackset creation.

## v1.0.0
    * Initial release.
