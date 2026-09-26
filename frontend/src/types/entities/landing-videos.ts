/** A clip of the landing page reel ("شاهد الواحة عن قرب"). */
export interface LandingVideo {
  id: number;
  title: string;
  description: string;
  /** `link`: YouTube / Vimeo / Bunny / direct mp4 URL. `upload`: file hosted on Cloudinary. */
  source: "link" | "upload";
  /** The URL to play: an embeddable page or a direct video file. */
  video_url: string;
  poster: string | null;
  duration_seconds: number;
  order: number;
}
