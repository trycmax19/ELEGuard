
import time
from datetime import datetime

import cv2
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_webrtc import (
    RTCConfiguration,
    WebRtcMode,
    webrtc_streamer,
)

from alerts import AlertManager
from config import (
    APP_NAME,
    DEFAULT_ALERT_COOLDOWN,
    DEFAULT_CONFIDENCE,
    SAFETY_NOTICE,
)
from database import (
    acknowledge_event,
    export_events_csv,
    get_events,
    init_db,
    log_event,
)
from detector import detect_image, load_model


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🐘",
    layout="wide",
)

init_db()

# Reuse the loaded model across Streamlit reruns.
@st.cache_resource(show_spinner="Loading YOLO model...")
def get_model():
    return load_model()


st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101b19, #142522);
}
h1, h2, h3, p, label {
    color: #edf5ef;
}
div[data-testid="stMetric"] {
    background: #203630;
    border: 1px solid #385448;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🐘 EleGuard AI")
st.caption("AI-powered elephant monitoring prototype")

st.warning(SAFETY_NOTICE)

with st.sidebar:
    st.header("Monitoring settings")

    confidence = st.slider(
        "Detection confidence threshold",
        min_value=0.10,
        max_value=0.90,
        value=DEFAULT_CONFIDENCE,
        step=0.05,
    )

    cooldown = st.slider(
        "Alert cooldown (seconds)",
        min_value=5,
        max_value=120,
        value=DEFAULT_ALERT_COOLDOWN,
        step=5,
    )

    st.divider()
    st.write("Model: YOLO11n")
    st.write("Detection target: Elephant")
    st.write("Camera: Browser webcam")
    st.caption(
        "Allow camera access when your browser requests permission."
    )

tab_live, tab_image, tab_history, tab_about = st.tabs([
    "📹 Live monitoring",
    "🖼️ Test an image",
    "📋 Event history",
    "ℹ️ About",
])

with tab_live:
    st.subheader("Live camera detection")
    st.write(
        "Click START and allow webcam access. "
        "The camera feed is processed locally by the Python app."
    )

    try:
        model = get_model()

        ctx = webrtc_streamer(
            key="eleguard-live-camera",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=lambda: __import__(
                "detector"
            ).ElephantVideoProcessor(
                model=model,
                confidence=confidence,
                cooldown=cooldown,
            ),
            media_stream_constraints={
                "video": True,
                "audio": False,
            },
            rtc_configuration=RTCConfiguration({
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun.l.google.com:19302"
                        ]
                    }
                ]
            }),
            async_processing=True,
        )

        if ctx.state.playing:
            st.success("Camera session is running.")

            @st.fragment(run_every=1)
            def show_detection_alert():
                processor = ctx.video_processor
                detection = (
                    processor.get_latest_detection()
                    if processor is not None
                    else None
                )

                if detection:
                    st.error(
                        f"ELEPHANT ALERT: {detection['count']} "
                        "elephant detected in the live camera feed."
                    )
                    st.write(
                        "Highest confidence: "
                        f"{detection['confidence']:.1%}"
                    )
                else:
                    st.success("No elephant detected in the current frame.")

            show_detection_alert()
        else:
            st.info(
                "Camera is stopped. Click START in the video panel."
            )

    except Exception as exc:
        st.error(f"Could not start the detector: {exc}")
        st.info(
            "Check the terminal for details, verify dependencies, "
            "and ensure yolo11n.pt can be downloaded."
        )

with tab_image:
    st.subheader("Test the detector with an image")
    st.write(
        "Upload a clear elephant image. This runs real model "
        "inference and saves an event only if an elephant is detected."
    )

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded_file is not None:
        original = Image.open(uploaded_file).convert("RGB")
        st.image(original, caption="Uploaded test image", width=500)

        if st.button("Run elephant detection", type="primary"):
            try:
                model = get_model()
                image_bgr = cv2.cvtColor(
                    __import__("numpy").array(original),
                    cv2.COLOR_RGB2BGR,
                )

                with st.spinner("Running AI detection..."):
                    result = detect_image(
                        image_bgr,
                        model,
                        confidence,
                    )

                annotated_rgb = cv2.cvtColor(
                    result["image"],
                    cv2.COLOR_BGR2RGB,
                )
                st.image(
                    annotated_rgb,
                    caption="AI detection result",
                    width=700,
                )

                if result["count"] > 0:
                    st.error(
                        f"Elephant detected: {result['count']}"
                    )
                    st.write(
                        "Highest confidence: "
                        f"{result['confidence']:.1%}"
                    )
                    log_event(
                        event_type="ELEPHANT_DETECTED",
                        count=result["count"],
                        confidence=result["confidence"],
                        source="uploaded_image",
                    )
                    st.success("Detection event saved.")
                else:
                    st.info(
                        "No elephant detected in this image "
                        "at the selected confidence threshold."
                    )

            except Exception as exc:
                st.error(f"Image detection failed: {exc}")

with tab_history:
    st.subheader("Detection event history")

    col_refresh, col_export = st.columns([1, 1])

    with col_refresh:
        if st.button("🔄 Refresh event history"):
            st.rerun()

    with col_export:
        st.download_button(
            "⬇️ Export CSV",
            data=export_events_csv(),
            file_name="eleguard_events.csv",
            mime="text/csv",
        )

    # Demo events are explicitly marked as simulated.
    if st.button("🧪 Create demo alert"):
        log_event(
            event_type="SIMULATED_DEMO_ALERT",
            count=1,
            confidence=0.0,
            source="simulated_demo",
        )
        st.success("A simulated demo event was saved.")
        st.rerun()

    events = get_events()

    if events.empty:
        st.info(
            "No events saved yet. Run image detection or create "
            "a clearly labelled demo alert."
        )
    else:
        event_types = ["All"] + sorted(
            events["event_type"].dropna().unique().tolist()
        )
        selected_type = st.selectbox(
            "Filter by event type",
            event_types,
        )

        filtered = events.copy()

        if selected_type != "All":
            filtered = filtered[
                filtered["event_type"] == selected_type
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        pending = filtered[filtered["acknowledged"] == 0]

        if not pending.empty:
            selected_id = st.selectbox(
                "Select event to acknowledge",
                pending["id"].tolist(),
            )

            if st.button("Acknowledge selected event"):
                acknowledge_event(selected_id)
                st.success(f"Event #{selected_id} acknowledged.")
                st.rerun()

        st.subheader("Event trend")

        chart_data = events.copy()
        chart_data["timestamp"] = pd.to_datetime(
            chart_data["timestamp"],
            errors="coerce",
        )
        chart_data = chart_data.dropna(subset=["timestamp"])
        chart_data["date"] = (
            chart_data["timestamp"].dt.strftime("%Y-%m-%d")
        )

        if not chart_data.empty:
            daily = (
                chart_data.groupby(["date", "event_type"])
                .size()
                .reset_index(name="events")
            )

            fig = px.bar(
                daily,
                x="date",
                y="events",
                color="event_type",
                title="Saved events by date",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

with tab_about:
    st.subheader("Project overview")

    st.markdown("""
    **Problem:** Elephants may enter railway corridors and other
    human infrastructure areas, creating risks for wildlife and people.

    **Prototype solution:** A camera feed or uploaded image is
    analyzed by a pretrained YOLO object-detection model. Elephant
    detections can create timestamped records for review.

    **Workflow:**
    1. Capture a webcam frame or upload an image.
    2. Run object detection.
    3. Display bounding boxes and confidence.
    4. Save qualifying events.
    5. Review and export the event history.

    **Current limitations:**
    - The pretrained model may miss elephants or make false detections.
    - A webcam detection does not calculate physical distance.
    - No train-location feed, track sensor, or real corridor geofence
      is connected.
    - Alerts are not connected to railway signalling or emergency services.
    - This prototype is not validated for real railway operations.

    **Future work:** Validate a dedicated wildlife model, add approved
    field-camera hardware, integrate authorized train-position data,
    and evaluate alert quality with railway and wildlife experts.
    """)

st.divider()
st.caption(
    f"{APP_NAME} | Student hackathon prototype | "
    f"Page loaded at {datetime.now().astimezone().strftime('%H:%M:%S')}"
)
