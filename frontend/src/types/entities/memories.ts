export interface MemoryParticipant {
  id: string;
  name: string;
  type: "child" | "student";
}

export interface MemoryListItem {
  id: string;
  media_type: "image" | "video";
  file_url: string;
  thumbnail_url: string | null;
  caption: string;
  uploader_name: string;
  created_at: string;
  tagged_participants: MemoryParticipant[];
  is_active: boolean;
}

export interface ParticipantSearchResult {
  id: string;
  name: string;
  code: string;
  type: "child" | "student";
}
