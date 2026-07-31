import { isPermissionGranted, requestPermission, sendNotification } from "@tauri-apps/plugin-notification";

async function ensurePermission(): Promise<boolean> {
  try {
    let granted = await isPermissionGranted();
    if (!granted) {
      granted = (await requestPermission()) === "granted";
    }
    return granted;
  } catch {
    return false;
  }
}

/** OS 네이티브 알림 전송 (권한 없으면 조용히 무시) */
export async function notify(title: string, body: string): Promise<void> {
  try {
    if (!(await ensurePermission())) return;
    sendNotification({ title, body });
  } catch {
    /* ignore */
  }
}
