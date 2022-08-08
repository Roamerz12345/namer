"""
Namer Configuration readers/verifier
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from requests_cache import CachedSession


# noinspection PyDataclass
@dataclass(init=False, repr=False, eq=True, order=False, unsafe_hash=True, frozen=False)
class NamerConfig:
    """
    Configuration for namer and namer_watchdog
    """

    # pylint: disable=too-many-instance-attributes

    porndb_token: str
    """
    token to access porndb.
    sign up here: https://metadataapi.net/
    """

    name_parser: str = "{_site}{_optional_date}{_sep}{_ts}{_name}{_dot}{_ext}"
    """
    This config may be a regex you provide, or a set of token used to build a regex.

    By default names are of the form:
    ``Site.YYYY.MM.DD.TS.scene.name.mkv``,``Site.YYYY.MM.DD.scene.name.mkv``,``Site.TS.scene.name.mkv``,``Site.scene.name.mkv``

     Supported token:
    ```
    _sep            r'[\\.\\- ]+'
    _site           r'(?P<site>[a-zA-Z0-9\\.\\-\\ ]*?[a-zA-Z0-9]*?)'
    _date           r'(?P<year>[0-9]{2}(?:[0-9]{2})?)[\\.\\- ]+(?P<month>[0-9]{2})[\\.\\- ]+(?P<day>[0-9]{2})'
    _optional_date  r'(?:(?P<year>[0-9]{2}(?:[0-9]{2})?)[\\.\\- ]+(?P<month>[0-9]{2})[\\.\\- ]+(?P<day>[0-9]{2})[\\.\\- ]+)?'
    _ts             r'((?P<trans>[T|t][S|s])'+_sep+'){0,1}'
    _name           r'(?P<name>(?:.(?![0-9]{2,4}[\\.\\- ][0-9]{2}[\\.\\- ][0-9]{2}))*)'
    _dot            r'\\.'
    _ext            r'(?P<ext>[a-zA-Z0-9]{3,4})$'
    ```

    The parts extracted from the file will be used in matching.
    _ts  is optional, and is mostly useful in stripping the marker from the _name, aiding in matching.
    _date if present is used to ensure the match is within 24 hours of your date.
    If the year/month/day capture groups are not present (due to you not using the supplied _date regex)
    dates will not be used in matching, possibly allowing false positives.
    """

    inplace_name: str = "{site} - {date} - {name}.{ext}"
    """
    How to write output file name.  When namer.py is run this is applied in place
    (next to the file to be processed).
    When run from namer_watchdog.py this will be written in to the success dir.

    Supports stand python 3 formatting, as well as:
    * a prefix:
    {site: 1p} - in this case put one space in front of the 'site', so ' Vixen'
    * a suffix:
    {date:_1s} - in this case put one underscore after the 'date', so '2020-01-01_'
    * an infix:
    {date:_2i} - in this case put two underscore before and after the 'date', so '__2020-01-01__'

    Examples:
    * {site} - {date} - {scene}.{ext}
    * {site}/{date}.{scene}.{ext}

    Missing values will be ignored.

    Allowed replacements:

    * 'date' - in the format of YYYY-MM-DD.
    * 'description' - too long, don't use in a name.
    * 'name' - the scene name
    * 'site' - the site name, BrazzersExxtra, AllHerLuv, Deeper, etc with spaces removed.
    * 'full_site' - the site name from porndb, unmodified, i.e: Brazzers Exxtra, All Her Luv, etc.
    * 'performers' - space seperated list of female performers
    * 'all_performers' - space seperated list of all performers
    * 'act' - an act, parsed from original file name, don't use.
    * 'ext' - original file's extension, you should keep this.
    * 'trans' - 'TS', or 'ts' if detected in original file name.

    """

    min_file_size: int = 300
    """
    minimum file size to process in MB, ignored if a file is to be processed
    """

    preserve_duplicates: bool = True
    """
    should duplicate videos be preserved.
    If false, duplicates will be verified with a perceptual hash, then compared via ffprobe.
    * First any movie under two minutes is ignored and presumed to be a sample,
    * then the highest resolution video is selected
    * then the best encoding mechanism h.245, or hvec.
    You can set minfile size to 0 if you have set
    """

    max_desired_resolutions: int = -1
    """
    Videos above this resolution will not be retained if the exact match to your resolution (or less) is available.
    List your desired resolution: 4380 2160 1080 or 720, -1 indicates that no max is desired.
    """

    desired_codec: List[str]
    """
    Listed in order, desired codecs defaults to "hvec h246", most videos are still in h246 encoding.
    """

    prefer_dir_name_if_available: bool = True
    """
    If a directory name is to be preferred over a file name.
    """

    target_extensions: List[str]
    """
    File types namer targets, only 'mp4's can be tagged, others can be renamed.
    """

    write_namer_log: bool = False
    """
    Should a log of comparisons be written next to processed video files.
    """

    write_namer_failed_log: bool = True
    """
    Should a log of comparisons be written next to processed video files.
    """

    update_permissions_ownership: bool = False
    """
    Should file permissions/ownership be updated.
    If false, set_uid/set_gid,set_dir_permissions,set_file_permissions will be ignored
    """

    set_uid: Optional[int] = None
    """
    UID Settings for new/moved files/dirs.
    """

    set_gid: Optional[int] = None
    """
    GID Settings for new/moved files/dirs.
    """

    set_dir_permissions: Optional[int] = 775
    """
    Permissions Settings for new/moved dirs.
    """

    set_file_permissions: Optional[int] = 664
    """
    Permissions Settings for new/moved file.
    """

    max_performer_names: int = 6
    """
    When guessing at matches namer can use performer names to attempt to match.   This can be costly in terms of cpu time.
    Plus who lists all the performers if over 6 on a scene's name?   You can increase this, but the cpu/runtime cost increases
    rapidly (combinatorial)
    """

    write_nfo: bool = False
    """
    Write an nfo file next to the directory in an emby/jellyfin readable format.
    """

    trailer_location: Optional[str] = None
    """
    If you want the trailers downloaded set the value relative to the final location of the movie file here.
    Plex:      Trailers/trailer.{ext}, or extras/Trailer-trailer.{ext}
    Jellyfin:  trailer/trailer.{ext}
    Extensions are handled by the download's mime type.
    Leave empty to not download trailers.
    """

    sites_with_no_date_info: Sequence[str]
    """
    A list of site names that do not have proper date information in them.   This is a problem with some tpdb
    scrapers/storage mechanisms.
    """

    enabled_requests_cache: bool = True
    """
    Cache http requests
    """

    requests_cache_expire_minutes: int = 10
    """
    Amount of minutes that http request would be in cache
    """

    override_tpdb_address: str = "https://api.metadataapi.net"
    """
    Used only for testing, can override the location of the porn database - usually to point at a locally
    running server that responds like tpdb to predefined queries.
    """

    enabled_tagging: bool = True
    """
    Currently metadata pulled from the porndb can be added to mp4 files.
    This metadata will be read in fully by Plex, and Apple TV app, partially by Jellyfin (no artist support).
    Metadata includes, Title, Release Date, Scene Name, Artist, Source URL, XXX Movie rating.
    If a file is an mkv adding metadata at this time isn't supported.

    Should metadata fetched from the porn db be written in to the metadata of the mp4.
    No flags in this section will be used if this is not set to true.
    """

    enabled_poster: bool = True
    """
    Should the poster fetched from the porn db be written in to the metadata of the mp4.
    This poster will be displayed in Plex, Jellyfin and Apple TV app.
    Only applicable if enabled_tagging is True
    """

    enable_metadataapi_genres: bool = False
    """
    Should genres pulled from the porndb be added to the file?   These genres are noisy and
    not recommend for use.  If this is false a single default genre will be used.
    """

    default_genre: str = "Adult"
    """
    If genre's are not copied this is the default genre added to files.
    Default value is adult.
    """

    language: Optional[str] = None
    """
    if language is set it will be used to select the default audio stream in an mp4 that has too many default stream
    to play correct in quicktime/apple tv.   If the language isn't found or is already the only default no action is
    taken, no streams (audio/video) are re-encoded.  Available here: https://iso639-3.sil.org/code_tables/639/data/
    """

    ignored_dir_regex: str = ".*_UNPACK_.*"
    """
    If a file found in the watch dir matches this regex it will be ignored, useful for some file processes.
    """

    new_relative_path_name: str = "{site} - {date} - {name}/{site} - {date} - {name}.{ext}"
    """
    like inplace_name above used for local call for renaming, this instead is used to move a file/dir to a location relative
    to the dest_dir below on successful matching/tagging.
    """

    del_other_files: bool = False
    """
    when processing a directory in the dest dir, should extra files besides the largest video be removed?
    or attempt to move them to a subdirectory specified in new_relative_path_name, if one exist.
    """

    watch_dir: Path
    """
    If running in watchdog mode, director where new downloads go.
    """

    work_dir: Path
    """
    If running in watchdog mode, temporary directory where work is done.
    a log file shows attempted matches and match closeness.
    """

    failed_dir: Path
    """
    If running in watchdog mode, Should processing fail the file or directory is moved here.
    Files can be manually moved to watch-dir to force reprocessing.
    """

    dest_dir: Path
    """
    If running in watchdog mode, dir where finalized files get written.
    """

    retry_time: str
    """
    Time to retry failed items every day.
    """

    extra_sleep_time: int = 30
    """
    Extra time to sleep in seconds to allow all information to be copied in dir
    """

    web: bool = True
    """
    Run webserver while running watchdog
    """

    port: int = 6980
    """
    Web server port
    """

    host: str = "0.0.0.0"
    """
    Web server host
    """

    web_root: Optional[str] = None
    """
    webroot (root url to place pages), useful for reverse proxies
    """

    allow_delete_files: bool = False
    """
    Allow to delete files in web interface
    """

    cache_session: Optional[CachedSession]
    """
    If enabled_requests_cache is true this http.session will be constructed and used for requests to tpdb.
    """

    diagnose_errors: bool = False
    """
    Errors may be raised by the program, and when they are loguru may be used to help explain them, showing
    values in the stack trace, potentially including the porndb token, this setting should only be turned on
    if you are going to check an logs you share for your token.
    """

    def __init__(self):
        if sys.platform != "win32":
            self.set_uid = os.getuid()
            self.set_gid = os.getgid()

    def __str__(self):
        config = self.to_dict()

        output = []
        for key in config:
            output.append(f"{key}:")
            for value in config[key]:
                output.append(f"  {value}: {config[key][value]}")

        # return json.dumps(config, indent=2)
        return '\n'.join(output)

    def to_dict(self) -> dict:
        porndb_token = "None In Set, Go to https://metadatapi.net/ to get one!"
        if self.porndb_token is not None:
            porndb_token = "*" * len(self.porndb_token)

        config = {
            "Namer Config": {
                "porndb_token": porndb_token,
                "inplace_name": self.inplace_name,
                "prefer_dir_name_if_available": self.prefer_dir_name_if_available,
                "target_extensions": self.target_extensions,
                "write_namer_log": self.write_namer_log,
                "write_namer_failed_log": self.write_namer_failed_log,
                "trailer_location": self.trailer_location,
                "sites_with_no_date_info": self.sites_with_no_date_info,
                "update_permissions_ownership": self.update_permissions_ownership,
                "set_dir_permissions": self.set_dir_permissions,
                "set_file_permissions": self.set_file_permissions,
                "set_uid": self.set_uid,
                "set_gid": self.set_gid,
                "max_performer_names": self.set_file_permissions,
                "enabled_requests_cache": self.enabled_requests_cache,
                "requests_cache_expire_minutes": self.requests_cache_expire_minutes,
                "override_tpdb_address": self.override_tpdb_address
            },
            "Duplicate Config": {
                "preserve_duplicates": self.preserve_duplicates,
                "max_desired_resolutions": self.max_desired_resolutions,
                "desired_codec": self.desired_codec,
            },
            "Tagging Config": {
                "write_nfo": self.write_nfo,
                "enabled_tagging": self.enabled_tagging,
                "enabled_poster": self.enabled_poster,
                "enable_metadataapi_genres": self.enable_metadataapi_genres,
                "default_genre": self.default_genre,
                "language": self.language,
            },
            "Watchdog Config": {
                "ignored_dir_regex": self.ignored_dir_regex,
                "min_file_size": f"{self.min_file_size} MB",
                "del_other_files": self.del_other_files,
                "new_relative_path_name": self.new_relative_path_name,
                "watch_dir": str(self.watch_dir),
                "work_dir": str(self.work_dir),
                "failed_dir": str(self.failed_dir),
                "dest_dir": str(self.dest_dir),
                "retry_time": self.retry_time,
                "extra_sleep_time": self.extra_sleep_time,
                "web": self.web,
                "port": self.port,
                "host": self.host,
                "web_root": self.web_root,
                "allow_delete_files": self.allow_delete_files,
                "diagnose_errors": self.diagnose_errors,
            }
        }

        return config