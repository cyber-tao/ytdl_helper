"""YouTube downloader wrapper using yt-dlp.

This module provides a small command-line wrapper around ``yt_dlp`` to
download videos, subtitles and thumbnails with sensible defaults and
post-processing options.

FFmpeg integration
------------------

This module can automatically use FFmpeg for post-processing tasks such as
merging video and audio streams, adding subtitles, and more. To enable FFmpeg
support, make sure to have FFmpeg installed and accessible in your system's
PATH.

Module functions
----------------

- :func:`progress_hook` -- progress callback used by ``yt_dlp``
- :func:`build_ydl_opts` -- construct yt-dlp options dictionary
- :func:`download_videos` -- download a list of URLs using constructed options
- :func:`parse_args` -- parse CLI arguments
- :func:`main` -- entrypoint for command-line execution

"""

import argparse
import logging
import os
import sys
from typing import List, Optional

import yt_dlp


def progress_hook(d: dict):
	"""Progress hook for yt-dlp download events.

	This function is intended to be supplied to ``yt_dlp.YoutubeDL`` via the
	``progress_hooks`` option. It prints a simple progress line to stdout when
	status is ``downloading`` and logs filenames when the download or
	post-processing is finished.

	Parameters
	----------
	d : dict
		Dictionary provided by yt-dlp describing the download event. Common
		keys include ``status``, ``total_bytes``, ``total_bytes_estimate``,
		``downloaded_bytes``, ``speed``, ``eta``, and ``filename``.

	Returns
	-------
	None

	"""
	if d.get('status') == 'downloading':
		total = d.get('total_bytes') or d.get('total_bytes_estimate')
		downloaded = d.get('downloaded_bytes', 0)
		if total:
			pct = downloaded / total * 100
			speed = d.get('speed', 0)
			eta = d.get('eta', 0)
			sys.stdout.write(
				f'\rProgress {pct:5.1f}%  Speed {speed:.0f}B/s  ETA {eta}s'
			)
			sys.stdout.flush()
	elif d.get('status') in {'finished', 'post_process'}:
		filename = d.get('filename') or d.get('info_dict', {}).get('_filename')
		if filename:
			logging.info('Processed: %s', filename)


def build_ytdl_opts(
	output_dir: Optional[str],
	cookies_file: Optional[str],
	langs: List[str],
	ffmpeg_location: Optional[str],
	quiet: bool,
	auto_sub: bool,
	no_playlist: bool,
	playlist_items: Optional[str],
	write_infojson: bool,
	clean_infojson: bool,
):
	"""Build the options dictionary for ``yt_dlp.YoutubeDL``.

	Parameters
	----------
	output_dir : Optional[str]
		Path to the directory where downloaded files will be stored. If
		``None``, the current working directory is used.
	cookies_file : Optional[str]
		Path to a cookies file to be passed to yt-dlp. If ``None``, no cookie
		file is used.
	langs : List[str]
		List of subtitle language codes to request (e.g. ``['zh-Hans','en']``).
	ffmpeg_location : Optional[str]
		Path to a directory containing ffmpeg executables, passed to
		yt-dlp if provided.
	quiet : bool
		If ``True``, yt-dlp will run in quiet mode.
	auto_sub : bool
		If ``True``, enable automatic captions fallback (writeautomaticsub).
	no_playlist : bool
		If ``True``, disable playlist processing (download single videos only).
	playlist_items : Optional[str]
		Playlist item selector string (e.g. ``"1-5,7,10-"``) or ``None``.
	write_infojson : bool
		If ``True``, write an ``info.json`` file for each entry.
	clean_infojson : bool
		If ``True`` together with ``write_infojson``, clean redundant fields
		from the generated info.json.

	Returns
	-------
	dict
		A dictionary of options suitable to pass into ``yt_dlp.YoutubeDL``.

	"""
	ydl_opts = {
		'outtmpl': '%(uploader)s - %(title)s.%(ext)s',
		'windowsfilenames': True,
		**({'paths': {'home': output_dir}} if output_dir else {}),
		'format': 'bv*+ba/b',
		'merge_output_format': 'mp4',
		'writesubtitles': True,
		'embedsubtitles': True,
		'subtitleslangs': langs,
		'subtitlesformat': 'srt/best',
		'writethumbnail': True,
		'embedthumbnail': True,
		'retries': 10,
		'fragment_retries': 10,
		'continuedl': True,
		'concurrent_fragment_downloads': 5,
		'quiet': quiet,
		'no_warnings': False,
		'ignoreerrors': False,
		'progress_hooks': [progress_hook],
		'postprocessors': [
			{'key': 'FFmpegVideoRemuxer', 'preferedformat': 'mp4'},
			{'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
			{'key': 'EmbedThumbnail', 'already_have_thumbnail': True},
			{'key': 'FFmpegMetadata'},
		],
	}

	if cookies_file:
		ydl_opts['cookiefile'] = cookies_file
	if ffmpeg_location:
		ydl_opts['ffmpeg_location'] = ffmpeg_location

	if auto_sub:
		ydl_opts['writeautomaticsub'] = True

	if no_playlist:
		ydl_opts['noplaylist'] = True
	if playlist_items:
		ydl_opts['playlist_items'] = playlist_items

	if write_infojson:
		ydl_opts['writeinfojson'] = True
		if clean_infojson:
			ydl_opts['clean_infojson'] = True

	return ydl_opts


def download_videos(urls: List[str], args):
	"""Download a list of video or playlist URLs using yt-dlp.

	This function constructs yt-dlp options from the parsed CLI ``args`` and
	attempts to download each URL in ``urls``. Failures are collected and
	reported via logging.

	Parameters
	----------
	urls : List[str]
		List of video or playlist URLs to download.
	args : argparse.Namespace
		Parsed arguments (as returned by :func:`parse_args`). Expected attributes
		include ``output_dir``, ``cookies``, ``langs``, ``ffmpeg``, ``quiet``,
		``auto_sub``, ``no_playlist``, ``playlist_items``, ``write_infojson`` and
		``clean_infojson``.

	Returns
	-------
	None

	Side effects
	------------
	Logs progress and writes downloaded files to disk via yt-dlp.

	"""
	ydl_opts = build_ytdl_opts(
		output_dir=args.output_dir,
		cookies_file=args.cookies
		if (args.cookies and os.path.isfile(args.cookies))
		else None,
		langs=args.langs,
		ffmpeg_location=args.ffmpeg,
		quiet=args.quiet,
		auto_sub=args.auto_sub,
		no_playlist=args.no_playlist,
		playlist_items=args.playlist_items,
		write_infojson=args.write_infojson,
		clean_infojson=args.clean_infojson,
	)

	logging.debug(
		'ydl_opts: %s',
		{
			k: ydl_opts[k]
			for k in (
				'format',
				'merge_output_format',
				'writesubtitles',
				'embedsubtitles',
				'subtitleslangs',
				'writethumbnail',
				'embedthumbnail',
				'retries',
				'continuedl',
				'concurrent_fragment_downloads',
			)
			if k in ydl_opts
		},
	)

	failed: List[str] = []
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		for url in urls:
			try:
				info = ydl.extract_info(url, download=True)
				filepath = ydl.prepare_filename(info)
				logging.info('Downloaded: %s', filepath)
			except Exception as e:
				logging.exception('Download failed: %s | URL: %s', e, url)
				failed.append(url)

	if failed:
		logging.warning(
			'The following %d URLs failed to download:\n%s',
			len(failed),
			'\n'.join(failed),
		)


def parse_args(argv: List[str]):
	"""Parse command-line arguments for the downloader.

	Parameters
	----------
	argv : List[str]
		List of command-line arguments (typically ``sys.argv[1:]``).

	Returns
	-------
	argparse.Namespace
		Parsed arguments with normalized fields. Notable post-processing:
		``langs`` is converted from a comma-separated string to ``List[str]``.
		If the provided cookies file path does not exist, ``cookies`` will be
		set to ``None`` and a warning will be emitted.

	"""
	parser = argparse.ArgumentParser(description='YouTube downloader (yt-dlp wrapper)')
	parser.add_argument('urls', nargs='+', help='One or more video/playlist URLs')
	parser.add_argument(
		'-o',
		'--output-dir',
		default=None,
		help='Output directory (defaults to current directory)',
	)
	parser.add_argument(
		'-c', '--cookies', default=None, help='Path to cookies file (optional)'
	)
	parser.add_argument(
		'-l',
		'--langs',
		default='zh-Hans,zh,zh-CN,en',
		help='Subtitle languages, comma-separated, e.g.: zh-Hans,zh,en',
	)
	parser.add_argument(
		'--ffmpeg',
		default=None,
		help='Directory containing FFmpeg executables (optional)',
	)
	parser.add_argument(
		'-q', '--quiet', action='store_true', help='Quiet mode; reduce output'
	)
	parser.add_argument(
		'--log-level',
		default='INFO',
		choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
		help='Log level',
	)
	parser.add_argument(
		'--auto-sub',
		action='store_true',
		help='Enable automatic captions when no manual subtitles are available (writeautomaticsub)',
	)
	parser.add_argument(
		'--no-playlist',
		action='store_true',
		help='Download single video only; ignore playlists',
	)
	parser.add_argument(
		'--playlist-items', default=None, help='Select playlist items, e.g.: 1-5,7,10-'
	)
	parser.add_argument(
		'--write-infojson', action='store_true', help='Write info.json for each entry'
	)
	parser.add_argument(
		'--clean-infojson',
		action='store_true',
		help='Clean redundant fields in info.json (with --write-infojson)',
	)
	args = parser.parse_args(argv)

	args.langs = [s.strip() for s in args.langs.split(',') if s.strip()]

	if args.cookies and not os.path.isfile(args.cookies):
		logging.warning(
			'The specified cookies file does not exist and will be ignored: %s',
			args.cookies,
		)
		args.cookies = None

	return args


def main(argv: Optional[List[str]] = None):
	"""Entry point for command-line execution.

	Parameters
	----------
	argv : Optional[List[str]]
		Optional list of command-line arguments. If omitted, ``sys.argv[1:]`` is
		used.

	Returns
	-------
	None

	Side effects
	------------
	Configures basic logging and invokes :func:`download_videos`.

	"""
	argv = argv if argv is not None else sys.argv[1:]
	args = parse_args(argv)

	logging.basicConfig(
		level=getattr(logging, args.log_level), format='[%(levelname)s] %(message)s'
	)

	download_videos(args.urls, args)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		logging.info('Interrupted by user. Exiting.')
