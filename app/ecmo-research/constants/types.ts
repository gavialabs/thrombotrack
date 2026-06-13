/**
 * Types for the frontend.
 *
 * Should essentially mirror the API models.py + schemas.py.
 */

export enum OxygenatorType {
  HLS = "hls",
  NAUTILUS = "nautilus",
}

export type Oxygenator = {
  id?: string;
  name: string;
  type: OxygenatorType;
  thumbnail: string | null;
  clot_area: number | null;
  fibrin_area: number | null;
  imaged_at: string | null;
  annotated_by: string | null;
};

export type OxygenatorImage = {
  id: string;
  cropped: string;
  thumbnail: string;
  mimetype: string;
  current_annotation_session_id: string;
  created_at: string;
  mask: string;
};

export type AnnotationSession = {
  imaged_at: string;
  clot_area: number;
  fibrin_area: number;
};

export type Annotation = {
  mask: string;
};
