use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{Emitter, Manager, WindowEvent};

/// 클릭 통과 모드 활성 여부를 백그라운드 폴링 스레드와 공유
struct ClickThrough(Arc<AtomicBool>);

/// 클릭 통과 모드 on/off. 켜지면 폴링 스레드가 커서 위치를 감시하며
/// 커서가 창 위에 있을 때만 이벤트를 통과시킨다.
#[tauri::command]
fn set_click_through(
    state: tauri::State<'_, ClickThrough>,
    window: tauri::WebviewWindow,
    enable: bool,
) {
    state.0.store(enable, Ordering::Relaxed);
    if !enable {
        let _ = window.set_ignore_cursor_events(false);
        let _ = window.emit("occlusion-cursor", false);
    }
}

fn show_main(app: &tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.show();
        let _ = win.unminimize();
        let _ = win.set_focus();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let active = Arc::new(AtomicBool::new(false));

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .manage(ClickThrough(active.clone()))
        .setup(move |app| {
            // ── 시스템 트레이 ──
            let show_i = MenuItem::with_id(app, "show", "열기", true, None::<&str>)?;
            let startpause_i = MenuItem::with_id(app, "startpause", "시작 / 정지", true, None::<&str>)?;
            let reset_i = MenuItem::with_id(app, "reset", "리셋", true, None::<&str>)?;
            let occ_off_i = MenuItem::with_id(app, "occlusion_off", "가림 방지 해제", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "종료", true, None::<&str>)?;
            let sep = PredefinedMenuItem::separator(app)?;
            let sep2 = PredefinedMenuItem::separator(app)?;
            let menu = Menu::with_items(
                app,
                &[&show_i, &startpause_i, &reset_i, &sep, &occ_off_i, &sep2, &quit_i],
            )?;

            TrayIconBuilder::with_id("main-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Time Timer")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => show_main(app),
                    "startpause" => {
                        let _ = app.emit("tray-startpause", ());
                    }
                    "reset" => {
                        let _ = app.emit("tray-reset", ());
                    }
                    "occlusion_off" => {
                        show_main(app);
                        let _ = app.emit("tray-occlusion-off", ());
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        show_main(tray.app_handle());
                    }
                })
                .build(app)?;

            // ── 닫기 → 종료 대신 트레이로 숨김 ──
            if let Some(win) = app.get_webview_window("main") {
                let w = win.clone();
                win.on_window_event(move |event| {
                    if let WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = w.hide();
                    }
                });
            }

            // ── 전역 커서 위치 폴링: 클릭통과 모드일 때만 동작 ──
            let handle = app.handle().clone();
            let active = active.clone();
            std::thread::spawn(move || {
                let mut last_inside: Option<bool> = None;
                loop {
                    std::thread::sleep(Duration::from_millis(40));
                    if !active.load(Ordering::Relaxed) {
                        last_inside = None;
                        continue;
                    }
                    let Some(win) = handle.get_webview_window("main") else {
                        continue;
                    };
                    let (Ok(cursor), Ok(pos), Ok(size)) =
                        (handle.cursor_position(), win.outer_position(), win.outer_size())
                    else {
                        continue;
                    };
                    let inside = cursor.x >= pos.x as f64
                        && cursor.x <= pos.x as f64 + size.width as f64
                        && cursor.y >= pos.y as f64
                        && cursor.y <= pos.y as f64 + size.height as f64;
                    if last_inside != Some(inside) {
                        last_inside = Some(inside);
                        let _ = win.set_ignore_cursor_events(inside);
                        let _ = win.emit("occlusion-cursor", inside);
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![set_click_through])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
