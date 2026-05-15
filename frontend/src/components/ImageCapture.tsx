import { ChangeEvent, useEffect, useRef, useState } from "react";
import { ArrowPathIcon, CameraIcon, PhotoIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { validateImageFile } from "../validation";
import styles from "./ImageCapture.module.css";

type ImageCaptureProps = {
  disabled?: boolean;
  onImageReady: (image: File | Blob) => Promise<void>;
};

export default function ImageCapture({ disabled = false, onImageReady }: ImageCaptureProps) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState("");
  const [fileError, setFileError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | Blob | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  useEffect(() => {
    return () => {
      stream?.getTracks().forEach((track) => track.stop());
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl, stream]);

  async function startCamera() {
    setCameraError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("Camera capture is unavailable in this browser. Use image upload instead.");
      return;
    }

    try {
      const nextStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
      setStream(nextStream);
    } catch {
      setCameraError("Camera permission was blocked or unavailable. You can retry permission or upload an image.");
    }
  }

  async function captureStill() {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob) {
      setCameraError("Could not capture a still image. Try again.");
      return;
    }
    setSelectedImage(blob);
    setPreview(blob);
  }

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const validationError = await validateImageFile(file);
    setFileError(validationError);
    if (validationError) return;
    setSelectedImage(file);
    setPreview(file);
  }

  function setPreview(image: File | Blob) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(image));
  }

  function clearSelection() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl("");
    setSelectedImage(null);
    setFileError("");
  }

  async function submitImage() {
    if (!selectedImage) return;
    setIsSubmitting(true);
    try {
      await onImageReady(selectedImage);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className={styles.panel} aria-labelledby="image-capture-title">
      <div className={styles.header}>
        <h2 id="image-capture-title">Photo input</h2>
        <p>Capture a still image with the browser camera or upload one from your device.</p>
      </div>

      <div className={styles.controls}>
        <button type="button" onClick={() => void startCamera()} disabled={disabled} title="Start camera">
          <CameraIcon aria-hidden="true" />
          Start camera
        </button>
        <label className={styles.uploadButton} title="Upload image">
          <PhotoIcon aria-hidden="true" />
          Upload image
          <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={(event) => void handleFile(event)} disabled={disabled} />
        </label>
      </div>

      {cameraError ? (
        <div className={styles.errorRow}>
          <p>{cameraError}</p>
          <button type="button" onClick={() => void startCamera()} disabled={disabled}>
            <ArrowPathIcon aria-hidden="true" />
            Retry
          </button>
        </div>
      ) : null}
      {fileError ? <p className={styles.error}>{fileError}</p> : null}

      {stream ? (
        <div className={styles.cameraBox}>
          <video ref={videoRef} autoPlay playsInline muted aria-label="Camera preview" />
          <button type="button" onClick={() => void captureStill()} disabled={disabled}>
            <CameraIcon aria-hidden="true" />
            Take still
          </button>
        </div>
      ) : null}

      {previewUrl ? (
        <div className={styles.preview}>
          <img src={previewUrl} alt="Selected lesson source" />
          <div className={styles.previewActions}>
            <button type="button" onClick={clearSelection} disabled={isSubmitting}>
              <XMarkIcon aria-hidden="true" />
              Replace
            </button>
            <button type="button" onClick={() => void submitImage()} disabled={disabled || isSubmitting || !selectedImage}>
              {isSubmitting ? "Generating..." : "Generate lesson"}
            </button>
          </div>
        </div>
      ) : null}
      <canvas ref={canvasRef} hidden />
    </section>
  );
}
