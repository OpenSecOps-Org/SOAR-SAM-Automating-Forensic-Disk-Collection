# Change Log

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
