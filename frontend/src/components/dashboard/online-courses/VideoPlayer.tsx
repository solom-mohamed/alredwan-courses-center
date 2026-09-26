"use client";

import type { ReactNode } from "react";
import { VideoLectureItem } from "@/types/entities";

interface VideoPlayerProps {
  lecture: VideoLectureItem;
  /** Rendered instead of the player when the lecture has no embeddable video. Defaults to nothing. */
  fallback?: ReactNode;
}

const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtube-nocookie.com",
  "www.youtube-nocookie.com",
  "youtu.be",
]);

const VIMEO_HOSTS = new Set(["vimeo.com", "www.vimeo.com", "player.vimeo.com"]);

const BUNNY_HOSTS = new Set(["iframe.mediadelivery.net", "video.bunnycdn.com"]);

function parseUrl(raw: string): URL | null {
  try {
    const url = new URL(raw);
    return url.protocol === "https:" || url.protocol === "http:" ? url : null;
  } catch {
    return null;
  }
}

function getYouTubeEmbedUrl(url: URL): string | null {
  if (!YOUTUBE_HOSTS.has(url.hostname)) return null;

  let videoId: string | null = null;

  if (url.hostname === "youtu.be") {
    videoId = url.pathname.split("/")[1] ?? null;
  } else if (url.pathname === "/watch") {
    videoId = url.searchParams.get("v");
  } else {
    const match = url.pathname.match(/^\/(?:embed|v|shorts|live)\/([\w-]{11})/);
    videoId = match ? match[1] : null;
  }

  if (!videoId || !/^[\w-]{11}$/.test(videoId)) return null;

  return `https://www.youtube-nocookie.com/embed/${videoId}?rel=0`;
}

function getVimeoEmbedUrl(url: URL): string | null {
  if (!VIMEO_HOSTS.has(url.hostname)) return null;

  // Matches vimeo.com/123, vimeo.com/video/123, player.vimeo.com/video/123,
  // vimeo.com/channels/x/123, vimeo.com/groups/x/videos/123, etc.
  const match = url.pathname.match(/(?:^|\/)(\d+)\/?$/);
  if (!match) return null;

  const params = new URLSearchParams();
  // Unlisted Vimeo videos carry a hash that the player needs.
  const hash = url.searchParams.get("h");
  if (hash && /^[\w-]+$/.test(hash)) params.set("h", hash);

  const query = params.toString();
  return `https://player.vimeo.com/video/${match[1]}${query ? `?${query}` : ""}`;
}

function getBunnyEmbedUrl(url: URL): string | null {
  if (!BUNNY_HOSTS.has(url.hostname)) return null;

  // Accept both the embed and the "play" page forms and normalise to /embed/.
  const match = url.pathname.match(/^\/(?:embed|play)\/([\w-]+)\/([\w-]+)\/?$/);
  if (!match) return null;

  const [, libraryId, videoId] = match;
  const params = new URLSearchParams();
  // Signed embeds carry a token/expiry pair that must be forwarded.
  for (const key of ["token", "expires"]) {
    const value = url.searchParams.get(key);
    if (value && /^[\w-]+$/.test(value)) params.set(key, value);
  }

  const query = params.toString();
  return `https://iframe.mediadelivery.net/embed/${libraryId}/${videoId}${
    query ? `?${query}` : ""
  }`;
}

/**
 * Builds a safe embed URL for a lecture. Only known video hosts are allowed:
 * anything else (or anything unparsable) yields `null` so the iframe never
 * receives an arbitrary URL.
 */
export function getEmbedUrl(lecture: VideoLectureItem): string | null {
  return getEmbedUrlForSource(lecture.video_url ?? "", lecture.video_platform);
}

/**
 * Same allow-list for any video link (landing clips, materials…): returns an
 * embeddable player URL for YouTube / Vimeo / Bunny, or `null` for anything
 * else so callers can fall back to a native `<video>` or a placeholder.
 */
export function getEmbedUrlForSource(
  rawSource: string,
  platform?: VideoLectureItem["video_platform"],
): string | null {
  const raw = rawSource.trim();
  if (!raw) return null;

  const url = parseUrl(raw);
  if (!url) return null;

  switch (platform) {
    case "youtube":
      return getYouTubeEmbedUrl(url);
    case "vimeo":
      return getVimeoEmbedUrl(url);
    case "bunny":
      return getBunnyEmbedUrl(url);
    default:
      // Unknown platform: still allow a recognised host, never a raw URL.
      return (
        getYouTubeEmbedUrl(url) ??
        getVimeoEmbedUrl(url) ??
        getBunnyEmbedUrl(url)
      );
  }
}

/** Placeholder for surfaces that want to say a lecture has no video (e.g. the studio). */
export function VideoUnavailable({ message }: { message?: string }) {
  return (
    <div className="shadow-soft grid aspect-video w-full place-items-center rounded-2xl bg-black p-4 text-center text-gray-400">
      <p className="text-xl font-medium break-words">
        {message ?? "لا يوجد فيديو متاح لهذه المحاضرة"}
      </p>
    </div>
  );
}

export default function VideoPlayer({
  lecture,
  fallback = null,
}: VideoPlayerProps) {
  const embedUrl = getEmbedUrl(lecture);

  if (!embedUrl) {
    return <>{fallback}</>;
  }

  return (
    <div className="shadow-soft relative aspect-video w-full overflow-hidden rounded-2xl bg-black">
      <iframe
        src={embedUrl}
        title={lecture.title}
        className="absolute inset-0 h-full w-full border-0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        sandbox="allow-scripts allow-same-origin allow-presentation allow-popups allow-forms"
        referrerPolicy="strict-origin-when-cross-origin"
        loading="lazy"
      />
    </div>
  );
}
