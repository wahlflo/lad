# lad (List All Data)
lad is a command line script to list directories and files including Alternate Data Streams by using the getfattr command.
The interface is inspired by the ls command.


## Installation

Install the package with pip

    pip install lad-cli

## Usage
Type ```lad --help``` to view the help.

```
usage: lad [OPTION]... [FILE]...

Lists information about the FILEs (the current directory by default) including Alternate Data Streams.

optional arguments:
  -h, --human-readable  print sizes like 1K 234M 2G etc.
  --help                prints the help text
  -R, --recursive       list subdirectories recursively
  --full-time           Shows the complete timestamp
  -n, --numeric-uid-gid
                        list numeric user and group IDs
  -F                    Show only files which include Alternate Data Streams
  --no-warning          Suppress warnings (e.g. if the filesystem is not NTFS)
```

## Examples

### Example 1

```
$ lad /mnt/usb
drwxrwxrwx root root    0 15. May 21:30 ABC
drwxrwxrwx root root    0 15. May 19:59 System Volume Information
-rwxrwxrwx root root   10 16. May 14:51 test.txt
-rwxrwxrwx root root   22 16. May 14:51 test.txt:secret
```

### Example 2
Scan recursively all subdirectories using the -R option flag.
```
$ lad /mnt/usb -R
drwxrwxrwx root root  0 15. May 21:30 ABC
-rwxrwxrwx root root  7 15. May 21:30 ABC/hello
-rwxrwxrwx root root  7 15. May 21:30 ABC/hello:secret2
drwxrwxrwx root root  0 15. May 19:59 System Volume Information
-rwxrwxrwx root root 76 15. May 19:59 System Volume Information/IndexerVolumeGuid
-rwxrwxrwx root root 12 15. May 19:59 System Volume Information/WPSettings.dat
-rwxrwxrwx root root 10 16. May 14:51 test.txt
-rwxrwxrwx root root 22 16. May 14:51 test.txt:secret
```

### Example 2
Show only files which contain an Alternate Data Stream using the -F option flag:
```
$ lad /mnt/usb -RF
-rwxrwxrwx root root  7 15. May 21:30 ABC/hello
-rwxrwxrwx root root  7 15. May 21:30 ABC/hello:secret2
-rwxrwxrwx root root 10 16. May 14:51 test.txt
-rwxrwxrwx root root 22 16. May 14:51 test.txt:secret
```

