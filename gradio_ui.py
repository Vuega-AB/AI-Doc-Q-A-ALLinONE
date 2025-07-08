import gradio as gr
import os
import json
from dotenv import load_dotenv
import re

# Ensure these imports point to your actual backend.py file and its functions
from backend import (
    get_unique_filenames_from_text_store,
    switch_db_backend,
    handle_pdf_upload_backend,
    chat_interface_backend,
    delete_files_backend,
    # Main config functions
    backend_get_initial_main_config,
    backend_update_main_config,
    backend_apply_uploaded_main_config,
    backend_generate_main_config_for_download,
    # Existing model info
    AVAILABLE_MODELS_NAMES,
    MODEL_NAME_TO_ID_MAP,
    MODEL_ID_TO_NAME_MAP,
    get_backend_initial_load_message,
    # NEW Scraper config functions (for managing categories and schedule)
    backend_get_current_scraper_payload,
    backend_add_update_scraper_category,
    backend_delete_scraper_category,
)
load_dotenv()
# FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://localhost:5000")
FLASK_BASE_URL = os.getenv("FLASK_BASE_URL")


def js_logout_function():
    flask_logout_url = f"{FLASK_BASE_URL}/logout"
    return f"() => {{ window.top.location.href = '{flask_logout_url}'; return []; }}"

def js_settings_function():
    flask_settings_url = f"{FLASK_BASE_URL}/settings"
    return f"() => {{ window.top.location.href = '{flask_settings_url}'; return []; }}"

def _show_status_popup(message, is_success):
    if message:
        if is_success: gr.Info(message)
        else: gr.Warning(message)

def get_initial_ui_data_for_gradio():
    initial_db_status_msg = get_backend_initial_load_message()
    initial_filenames_choices = get_unique_filenames_from_text_store()
    return initial_db_status_msg, initial_filenames_choices

CUSTOM_CSS = """
#app-header-row { position: sticky !important; top: 0; z-index: 100; width: 100% !important; box-sizing: border-box; }
#main-content-row { flex-grow: 1 !important; display: flex !important; flex-direction: row !important; padding: 20px !important; gap: 24px !important; overflow: hidden !important; min-height: 0 !important; width: 100% !important; box-sizing: border-box; }
.controls-column { flex: 0 0 650px !important; max-width: 700px !important; }
.chat-column { flex-grow: 1 !important; min-width: 300px !important; }
.category-section { border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom:15px; }
html.dark .category-section { border: 1px solid var(--dark-border-dm); }
.cron-explanation pre { white-space: pre-wrap; word-wrap: break-word; font-family: monospace; }
"""

CRON_EXPLANATION_MARKDOWN = """
A cron schedule expression has five fields that describe the schedule details.
`*` = always. It is a wildcard for every part of the cron schedule expression.
So `* * * * *` means **every minute** of **every hour** of **every day** of **every month** and **every day** of the **week**.

*The nice drawing above is provided by [wikipedia](https://en.wikipedia.org/wiki/Cron#CRON_expression).*
"""

def create_gradio_app():
    with gr.Blocks(css=CUSTOM_CSS, theme='lone17/kotaemon', title="IntelLaw Gradio") as demo:
        # --- States ---
        main_config_state = gr.State({})
        # This state will hold the entire scraper payload: {"categories": [...]}
        full_scraper_payload_state = gr.State({"categories": []}) 
        
        # New states for managing links in UI before saving
        new_category_links_list_state = gr.State([]) # Holds [{url: ..., scraper_type: ...}] for new category
        edit_category_links_list_state = gr.State([]) # Holds [{url: ..., scraper_type: ...}] for edited category

        # Helper to convert list of link dicts to list of lists for DataFrame
        def links_to_dataframe_data(links_list):
            return [[link['url'], link['scraper_type']] for link in links_list]
        
        # Helper to convert list of link dicts to choices for CheckboxGroup
        def links_to_checkbox_choices(links_list):
            return [f"{link['url']} ({link['scraper_type']})" for link in links_list]

        # Header
        with gr.Row(elem_id="app-header-row"):
            gr.Markdown("# 📄 IntelLaw", elem_id="app-title")
            with gr.Row():
                dummy = gr.Textbox(visible=False)
                settings_btn = gr.Button("Settings", elem_id="settings-btn", variant="secondary", visible=False)
                sign_out_btn = gr.Button("Sign Out", elem_id="actual-sign-out-btn", variant="secondary")
        settings_btn.click(fn=None, inputs=None, outputs=[dummy], js=js_settings_function())
        sign_out_btn.click(fn=None, inputs=None, outputs=[dummy], js=js_logout_function())

        # Main content
        with gr.Row(elem_id="main-content-row"):
            with gr.Column(elem_classes=["controls-column"], visible=False) as controls_column_element:
                gr.Markdown("### 🛠️ Controls")
                with gr.Accordion("Database Backend", open=True):
                    db_radio = gr.Radio(label="Choose Database", choices=["Dropbox", "MongoDB"], value="MongoDB")
                    db_status = gr.Textbox(label="DB Status", interactive=False)
                with gr.Tabs() as admin_tabs:
                    with gr.TabItem("⚙️ Main Config"):
                        gr.Markdown("### AI Model Configuration")
                        model_selector = gr.Dropdown(label="AI Models (Max 3)", choices=AVAILABLE_MODELS_NAMES, multiselect=True, max_choices=3, interactive=True)
                        vary_temp = gr.Checkbox(label="Vary Temperature", value=True)
                        temp_slider = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, step=0.01, value=0.7)
                        vary_top_p = gr.Checkbox(label="Vary Top-P", value=False)
                        top_p_slider = gr.Slider(label="Top-P", minimum=0.0, maximum=1.0, step=0.01, value=0.9)
                        system_prompt = gr.Textbox(label="System Prompt", lines=4, value="Answer questions strictly based on the provided context...")
                        gr.Markdown("---")
                        save_model_config_btn = gr.Button("Save Model & Prompt Settings", variant="primary")
                        main_config_feedback_text = gr.Textbox(label="Config Status", interactive=False, lines=2)
                        gr.Markdown("---")
                        gr.Markdown("#### Configuration File Management")
                        upload_main_config_btn = gr.UploadButton("Upload & Apply Main Config (JSON)", file_types=[".json"], variant="secondary", size="sm")
                        download_main_config_btn = gr.DownloadButton("Download Current Main Config", variant="secondary", size="sm")

                    # Merged tab: Sources & Schedule
                    with gr.TabItem("🔗 Sources & Schedule"):
                        gr.Markdown("### Manage Web Scraper Categories and Schedules")
                        scraper_status_text = gr.Textbox(label="Status", interactive=False, lines=2, placeholder="Operation status messages...")
                        
                        gr.Markdown("#### Current Scraper Configuration JSON")
                        current_scraper_config_json_display = gr.Code(label="Full Configuration", language="json", interactive=False)

                        with gr.Blocks(elem_classes="category-section"):
                            gr.Markdown("#### 1. Add New Category")
                            new_category_name = gr.Textbox(label="New Category Name (e.g., GDBR, EU-Law)", placeholder="Enter a unique name for the category")
                            with gr.Accordion("Category Schedule (Cron)", open=True) as new_category_schedule_group:
                                with gr.Row():
                                    new_cron_minute = gr.Textbox(label="Minute", placeholder="0-59", value="*/10", interactive=True)
                                    new_cron_hour = gr.Textbox(label="Hour", placeholder="0-23", value="*", interactive=True)
                                    new_cron_day_month = gr.Textbox(label="Day (Month)", placeholder="1-31", value="*", interactive=True)
                                    new_cron_month = gr.Textbox(label="Month", placeholder="1-12", value="*", interactive=True)
                                    new_cron_day_week = gr.Textbox(label="Day (Week)", placeholder="0-7", value="*", interactive=True)
                                with gr.Accordion("Cron Syntax Help", open=False, elem_classes="cron-explanation"):
                                   gr.Markdown(CRON_EXPLANATION_MARKDOWN)
                            
                            # New Link Input for Add Category
                            with gr.Accordion("Category Links", open=True) as new_category_links_group:
                                with gr.Row():
                                    new_link_url_input = gr.Textbox(label="Link URL", placeholder="https://example.com/file.pdf", scale=3)
                                    new_link_type_input = gr.Radio(label="Scraper Type", choices=["pdf", "text"], value="pdf", interactive=True, scale=1)
                                    add_single_new_link_btn = gr.Button("Add Link", variant="secondary", size="sm", scale=1)
                                new_links_dataframe = gr.DataFrame(
                                    headers=["URL", "Type"], 
                                    col_count=(2, "fixed"), 
                                    type="array", 
                                    interactive=False, 
                                    label="Links for New Category",
                                    value=links_to_dataframe_data(new_category_links_list_state.value), # Initialize from state
                                )
                                with gr.Row():
                                    new_links_to_delete_cbg = gr.CheckboxGroup(label="Select Links to Remove", choices=[], scale=3)
                                    delete_selected_new_links_btn = gr.Button("Remove Selected", variant="stop", size="sm", scale=1)
                                    clear_all_new_links_btn = gr.Button("Clear All", variant="stop", size="sm", scale=1)
                            add_category_btn = gr.Button("Add Category", variant="primary")

                        with gr.Blocks(elem_classes="category-section"):
                            gr.Markdown("#### 2. Edit Existing Category")
                            edit_category_dropdown = gr.Dropdown(label="Select Category to Edit", choices=[], interactive=True)
                            with gr.Group(visible=False) as edit_category_details_group:
                                edit_current_category_name = gr.Textbox(label="Category Name", interactive=False) # Display only
                                with gr.Accordion("Edit Schedule (Cron)", open=True) as edit_category_schedule_group:
                                    with gr.Row():
                                        edit_cron_minute = gr.Textbox(label="Minute", placeholder="0-59", interactive=True)
                                        edit_cron_hour = gr.Textbox(label="Hour", placeholder="0-23", interactive=True)
                                        edit_cron_day_month = gr.Textbox(label="Day (Month)", placeholder="1-31", interactive=True)
                                        edit_cron_month = gr.Textbox(label="Month", placeholder="1-12", interactive=True)
                                        edit_cron_day_week = gr.Textbox(label="Day (Week)", placeholder="0-7", interactive=True)
                                # New Link Input for Edit Category
                                with gr.Accordion("Edit Links", open=True) as edit_category_links_group:
                                    with gr.Row():
                                        edit_link_url_input = gr.Textbox(label="Link URL", placeholder="https://example.com/file.pdf", scale=3)
                                        edit_link_type_input = gr.Radio(label="Scraper Type", choices=["pdf", "text"], value="pdf", interactive=True, scale=1)
                                        add_single_edit_link_btn = gr.Button("Add Link", variant="secondary", size="sm", scale=1)
                                    edit_links_dataframe = gr.DataFrame(
                                        headers=["URL", "Type"], 
                                        col_count=(2, "fixed"), 
                                        type="array", 
                                        interactive=False, 
                                        label="Links for Edited Category",
                                        value=links_to_dataframe_data(edit_category_links_list_state.value), # Initialize from state
                                    )
                                    with gr.Row():
                                        edit_links_to_delete_cbg = gr.CheckboxGroup(label="Select Links to Remove", choices=[], scale=3)
                                        delete_selected_edit_links_btn = gr.Button("Remove Selected", variant="stop", size="sm", scale=1)
                                        clear_all_edit_links_btn = gr.Button("Clear All", variant="stop", size="sm", scale=1)
                                update_category_btn = gr.Button("Update Category", variant="secondary")

                        with gr.Blocks(elem_classes="category-section"):
                            gr.Markdown("#### 3. Delete Categories")
                            delete_category_checkbox_group = gr.CheckboxGroup(label="Select Categories to Delete", choices=[], interactive=True)
                            delete_selected_categories_btn = gr.Button("Delete Selected Categories", variant="stop")

                    with gr.TabItem("📁 Stored Files"):
                        file_uploader = gr.Files(label="Upload PDFs", file_count="multiple", type="filepath", file_types=[".pdf"])
                        upload_status = gr.Textbox(label="Upload Status", interactive=False, lines=3)
                        files_to_delete_cbg = gr.CheckboxGroup(label="Select Files to Delete", choices=[], value=[])
                        delete_btn = gr.Button("Delete Selected", variant="stop", size="sm")
                        delete_status = gr.Textbox(label="Deletion Status", interactive=False, lines=2)
                    
            with gr.Column(elem_classes=["chat-column"]) as chat_column_element:
                gr.Markdown("### 💬 Chat Interface")
                chatbot = gr.Chatbot(value=[], label="IntelLaw Chatbot", show_copy_button=True, bubble_full_width=False, height=500)
                with gr.Row(elem_id="chat-input-container"):
                    chat_input = gr.Textbox(show_label=False, placeholder="Ask any question...", container=False)
                    send_btn = gr.Button("Send", variant="primary")

        # States and Load logic
        selected_db_state = gr.State("MongoDB")
        status_msg = gr.State(); success_flag = gr.State()

        # UI Helper Functions for Scraper Tab
        def _update_scraper_ui_choices_and_display(full_payload):
            categories = full_payload.get("categories", [])
            category_names = [cat["name"] for cat in categories]
            json_display = json.dumps(full_payload, indent=2)
            return (
                gr.update(choices=category_names, value=None), # edit dropdown
                gr.update(choices=category_names, value=[]),  # delete checkbox group
                json_display
            )
        
        def handle_visibility_and_initial_load(request: gr.Request):
            user_role = request.query_params.get("user_role", "user") if request and hasattr(request, "query_params") else "user"
            admin_view_visible = (user_role == "admin")
            db_msg, files_choices_init = get_initial_ui_data_for_gradio()
            
            # Load Main Config
            main_config_init = backend_get_initial_main_config()
            model_conf = main_config_init.get('model_config', {})
            sel_model_ids = model_conf.get("selected_models", [])
            initial_selected_model_names = [MODEL_ID_TO_NAME_MAP.get(mid) for mid in sel_model_ids if MODEL_ID_TO_NAME_MAP.get(mid)]
            
            # Load Scraper Payload
            initial_scraper_payload = backend_get_current_scraper_payload()
            edit_dd, remove_cbg, json_display = _update_scraper_ui_choices_and_display(initial_scraper_payload)

            return (
                gr.update(visible=admin_view_visible), gr.update(visible=admin_view_visible),
                db_msg, gr.update(choices=files_choices_init, value=[]), main_config_init,
                gr.update(value=initial_selected_model_names),
                model_conf.get("vary_temperature", True), model_conf.get("temperature", 0.7),
                model_conf.get("vary_top_p", False), model_conf.get("top_p", 0.9),
                model_conf.get("system_prompt", ""), 
                initial_scraper_payload, edit_dd, remove_cbg, json_display,
                [], # Reset new_category_links_list_state
                links_to_dataframe_data([]) # Reset new_links_dataframe
            )
        demo.load(
            fn=handle_visibility_and_initial_load, inputs=None, 
            outputs=[
                settings_btn, controls_column_element, db_status, files_to_delete_cbg, main_config_state,
                model_selector, vary_temp, temp_slider, vary_top_p, top_p_slider, system_prompt,
                full_scraper_payload_state, edit_category_dropdown, delete_category_checkbox_group, current_scraper_config_json_display,
                new_category_links_list_state, new_links_dataframe
            ]
        )

        # Event Handlers
        db_radio.change(fn=switch_db_backend, inputs=[db_radio, selected_db_state], outputs=[selected_db_state, db_status, files_to_delete_cbg])
        
        def handle_save_model_config(current_main_config, sel_models, vary_t, temp, vary_p, top_p, sys_prompt):
            updated_config = current_main_config.copy()
            sel_model_ids = [MODEL_NAME_TO_ID_MAP.get(name) for name in sel_models if MODEL_NAME_TO_ID_MAP.get(name)]
            if 'model_config' not in updated_config: updated_config['model_config'] = {}
            updated_config['model_config'].update({"selected_models": sel_model_ids, "vary_temperature": vary_t, "temperature": temp, "vary_top_p": vary_p, "top_p": top_p, "system_prompt": sys_prompt})
            success, msg, final_config = backend_update_main_config(updated_config)
            return msg, final_config if success else current_main_config
        save_model_config_btn.click(
            fn=handle_save_model_config,
            inputs=[main_config_state, model_selector, vary_temp, temp_slider, vary_top_p, top_p_slider, system_prompt],
            outputs=[main_config_feedback_text, main_config_state]
        )
        
        def update_ui_from_main_config(new_main_config):
            model_conf = new_main_config.get('model_config', {})
            sel_model_ids = model_conf.get("selected_models", [])
            sel_model_names = [MODEL_ID_TO_NAME_MAP.get(mid) for mid in sel_model_ids if MODEL_ID_TO_NAME_MAP.get(mid)]
            return (gr.update(value=sel_model_names), model_conf.get("vary_temperature", True), model_conf.get("temperature", 0.7), model_conf.get("vary_top_p", False), model_conf.get("top_p", 0.9), model_conf.get("system_prompt", ""))
        
        upload_main_config_btn.upload(fn=backend_apply_uploaded_main_config, inputs=[upload_main_config_btn], outputs=[status_msg, success_flag, main_config_state]
            ).then(fn=_show_status_popup, inputs=[status_msg, success_flag], outputs=None
            ).then(fn=update_ui_from_main_config, inputs=[main_config_state], outputs=[
                model_selector, vary_temp, temp_slider, vary_top_p, top_p_slider, system_prompt
            ])
            
        download_main_config_btn.click(fn=backend_generate_main_config_for_download, inputs=[main_config_state], outputs=[download_main_config_btn])
        file_uploader.upload(fn=handle_pdf_upload_backend, inputs=[file_uploader, selected_db_state], outputs=[upload_status, files_to_delete_cbg])
        delete_btn.click(fn=delete_files_backend, inputs=[files_to_delete_cbg, selected_db_state], outputs=[delete_status, files_to_delete_cbg])
        
        # --- Event Handlers for NEW Sources & Schedule Tab ---

        # Add New Category Links
        def add_single_link_to_new_category(url, link_type, current_links_list):
            if not url.strip():
                return current_links_list, gr.update(value=""), "URL cannot be empty."
            new_link = {"url": url.strip(), "scraper_type": link_type}
            # Check for duplicates before adding
            if new_link in current_links_list:
                return current_links_list, gr.update(value=""), "Link already added."
            
            updated_links = current_links_list + [new_link]
            return (
                updated_links, 
                gr.update(value=""), # Clear URL input
                links_to_dataframe_data(updated_links),
                gr.update(choices=links_to_checkbox_choices(updated_links), value=[]), # Update checkbox group
                "Link added successfully."
            )

        add_single_new_link_btn.click(
            fn=add_single_link_to_new_category,
            inputs=[new_link_url_input, new_link_type_input, new_category_links_list_state],
            outputs=[new_category_links_list_state, new_link_url_input, new_links_dataframe, new_links_to_delete_cbg, scraper_status_text]
        )

        def delete_selected_links_from_new_category(links_to_remove_str, current_links_list):
            if not links_to_remove_str:
                return current_links_list, links_to_dataframe_data(current_links_list), gr.update(choices=links_to_checkbox_choices(current_links_list), value=[]), "No links selected for removal."
            
            # Convert string representation back to dict for comparison
            # This relies on the format "URL (Type)" from links_to_checkbox_choices
            links_to_remove_parsed = []
            for s in links_to_remove_str:
                match = re.match(r"(.*) \((pdf|text)\)", s)
                if match:
                    links_to_remove_parsed.append({"url": match.group(1), "scraper_type": match.group(2)})

            updated_links = [link for link in current_links_list if link not in links_to_remove_parsed]
            
            return (
                updated_links, 
                links_to_dataframe_data(updated_links),
                gr.update(choices=links_to_checkbox_choices(updated_links), value=[]),
                f"Removed {len(links_to_remove_parsed)} link(s)."
            )

        delete_selected_new_links_btn.click(
            fn=delete_selected_links_from_new_category,
            inputs=[new_links_to_delete_cbg, new_category_links_list_state],
            outputs=[new_category_links_list_state, new_links_dataframe, new_links_to_delete_cbg, scraper_status_text]
        )

        def clear_all_links_new_category():
            return [], links_to_dataframe_data([]), gr.update(choices=[], value=[]), "All links cleared."

        clear_all_new_links_btn.click(
            fn=clear_all_links_new_category,
            inputs=None,
            outputs=[new_category_links_list_state, new_links_dataframe, new_links_to_delete_cbg, scraper_status_text]
        )

        # Add Category Button Logic
        def add_category_logic(payload_state, name, min, hour, dom, mon, dow, links_list):
            if not name.strip(): 
                return payload_state, "Category name cannot be empty.", gr.update(), gr.update(), gr.update(), gr.update(value=""), [], links_to_dataframe_data([]), gr.update(choices=[], value=[])
            if not links_list:
                return payload_state, "Category must have at least one link.", gr.update(), gr.update(), gr.update(), gr.update(value=""), [], links_to_dataframe_data([]), gr.update(choices=[], value=[])
            
            schedule = {"minute": min, "hour": hour, "day_of_month": dom, "month": mon, "day_of_week": dow}
            
            success, msg, new_payload = backend_add_update_scraper_category(name, schedule, links_list)
            
            edit_dd, del_cbg, json_display = _update_scraper_ui_choices_and_display(new_payload)
            return (
                new_payload, 
                msg, 
                edit_dd, 
                del_cbg, 
                json_display, 
                gr.update(value=""), # Clear new category name
                [], # Reset new_category_links_list_state
                links_to_dataframe_data([]), # Reset new_links_dataframe
                gr.update(choices=[], value=[]) # Reset new_links_to_delete_cbg
            )

        add_category_btn.click(
            fn=add_category_logic,
            inputs=[
                full_scraper_payload_state, new_category_name,
                new_cron_minute, new_cron_hour, new_cron_day_month, new_cron_month, new_cron_day_week,
                new_category_links_list_state # Now takes the state directly
            ],
            outputs=[full_scraper_payload_state, scraper_status_text, 
                     edit_category_dropdown, delete_category_checkbox_group, current_scraper_config_json_display,
                     new_category_name, new_category_links_list_state, new_links_dataframe, new_links_to_delete_cbg]
        )

        # Edit Existing Category Links & Info
        def on_edit_category_dropdown_change(selected_category_name, payload_state):
            if not selected_category_name:
                return gr.update(visible=False), None, "", "", "", "", "", [], links_to_dataframe_data([]), gr.update(choices=[], value=[])
            
            categories = payload_state.get("categories", [])
            selected_category = next((cat for cat in categories if cat["name"] == selected_category_name), None)

            if not selected_category:
                return gr.update(visible=False), None, "", "", "", "", "", [], links_to_dataframe_data([]), gr.update(choices=[], value=[])

            schedule = selected_category.get("schedule", {})
            links = selected_category.get("links", [])
            
            return (
                gr.update(visible=True),
                selected_category["name"], # Display name, not editable
                schedule.get("minute", "*"),
                schedule.get("hour", "*"),
                schedule.get("day_of_month", "*"),
                schedule.get("month", "*"),
                schedule.get("day_of_week", "*"),
                links, # Populate edit_category_links_list_state
                links_to_dataframe_data(links), # Populate edit_links_dataframe
                gr.update(choices=links_to_checkbox_choices(links), value=[]) # Populate edit_links_to_delete_cbg
            )

        edit_category_dropdown.change(
            fn=on_edit_category_dropdown_change,
            inputs=[edit_category_dropdown, full_scraper_payload_state],
            outputs=[
                edit_category_details_group, edit_current_category_name,
                edit_cron_minute, edit_cron_hour, edit_cron_day_month, edit_cron_month, edit_cron_day_week,
                edit_category_links_list_state, edit_links_dataframe, edit_links_to_delete_cbg
            ]
        )

        def add_single_link_to_edit_category(url, link_type, current_links_list):
            if not url.strip():
                return current_links_list, gr.update(value=""), "URL cannot be empty."
            new_link = {"url": url.strip(), "scraper_type": link_type}
            if new_link in current_links_list:
                return current_links_list, gr.update(value=""), "Link already added."
            
            updated_links = current_links_list + [new_link]
            return (
                updated_links, 
                gr.update(value=""), # Clear URL input
                links_to_dataframe_data(updated_links),
                gr.update(choices=links_to_checkbox_choices(updated_links), value=[]),
                "Link added successfully."
            )

        add_single_edit_link_btn.click(
            fn=add_single_link_to_edit_category,
            inputs=[edit_link_url_input, edit_link_type_input, edit_category_links_list_state],
            outputs=[edit_category_links_list_state, edit_link_url_input, edit_links_dataframe, edit_links_to_delete_cbg, scraper_status_text]
        )

        def delete_selected_links_from_edit_category(links_to_remove_str, current_links_list):
            if not links_to_remove_str:
                return current_links_list, links_to_dataframe_data(current_links_list), gr.update(choices=links_to_checkbox_choices(current_links_list), value=[]), "No links selected for removal."
            
            links_to_remove_parsed = []
            for s in links_to_remove_str:
                match = re.match(r"(.*) \((pdf|text)\)", s)
                if match:
                    links_to_remove_parsed.append({"url": match.group(1), "scraper_type": match.group(2)})

            updated_links = [link for link in current_links_list if link not in links_to_remove_parsed]
            
            return (
                updated_links, 
                links_to_dataframe_data(updated_links),
                gr.update(choices=links_to_checkbox_choices(updated_links), value=[]),
                f"Removed {len(links_to_remove_parsed)} link(s)."
            )

        delete_selected_edit_links_btn.click(
            fn=delete_selected_links_from_edit_category,
            inputs=[edit_links_to_delete_cbg, edit_category_links_list_state],
            outputs=[edit_category_links_list_state, edit_links_dataframe, edit_links_to_delete_cbg, scraper_status_text]
        )

        def clear_all_links_edit_category():
            return [], links_to_dataframe_data([]), gr.update(choices=[], value=[]), "All links cleared."

        clear_all_edit_links_btn.click(
            fn=clear_all_links_edit_category,
            inputs=None,
            outputs=[edit_category_links_list_state, edit_links_dataframe, edit_links_to_delete_cbg, scraper_status_text]
        )

        # Update Category Button Logic
        def update_category_logic(payload_state, selected_name, min, hour, dom, mon, dow, links_list):
            if not selected_name: 
                return payload_state, "No category selected for update.", gr.update(), gr.update(), gr.update(), gr.update(visible=False)
            if not links_list:
                return payload_state, "Category must have at least one link.", gr.update(), gr.update(), gr.update(), gr.update(visible=False)

            schedule = {"minute": min, "hour": hour, "day_of_month": dom, "month": mon, "day_of_week": dow}
            
            success, msg, new_payload = backend_add_update_scraper_category(selected_name, schedule, links_list)
            
            edit_dd, del_cbg, json_display = _update_scraper_ui_choices_and_display(new_payload)
            return (
                new_payload, 
                msg, 
                edit_dd, 
                del_cbg, 
                json_display, 
                gr.update(visible=False), # Hide the edit group after update
                [], # Reset edit_category_links_list_state
                links_to_dataframe_data([]), # Reset edit_links_dataframe
                gr.update(choices=[], value=[]) # Reset edit_links_to_delete_cbg
            )

        update_category_btn.click(
            fn=update_category_logic,
            inputs=[
                full_scraper_payload_state, edit_category_dropdown,
                edit_cron_minute, edit_cron_hour, edit_cron_day_month, edit_cron_month, edit_cron_day_week,
                edit_category_links_list_state # Now takes the state directly
            ],
            outputs=[full_scraper_payload_state, scraper_status_text, 
                     edit_category_dropdown, delete_category_checkbox_group, current_scraper_config_json_display,
                     edit_category_details_group, edit_category_links_list_state, edit_links_dataframe, edit_links_to_delete_cbg]
        )

        def delete_selected_categories_logic(payload_state, categories_to_delete):
            if not categories_to_delete:
                return payload_state, "No categories selected for deletion.", gr.update(), gr.update(), gr.update()
            
            current_payload = payload_state
            messages = []
            for category_name in categories_to_delete:
                success, msg, updated_payload = backend_delete_scraper_category(category_name)
                current_payload = updated_payload # Chain updates
                messages.append(f"'{category_name}': {msg}")
            
            edit_dd, del_cbg, json_display = _update_scraper_ui_choices_and_display(current_payload)
            return (
                current_payload, 
                "\n".join(messages), 
                edit_dd, 
                del_cbg, 
                json_display
            )
        
        delete_selected_categories_btn.click(
            fn=delete_selected_categories_logic,
            inputs=[full_scraper_payload_state, delete_category_checkbox_group],
            outputs=[full_scraper_payload_state, scraper_status_text, 
                     edit_category_dropdown, delete_category_checkbox_group, current_scraper_config_json_display]
        )

        def run_chat(user_input, history, db_state_val, main_config_val):
            model_config = main_config_val.get('model_config', {})
            return chat_interface_backend(user_input, history, db_state_val, model_config)
        chat_inputs = [chat_input, chatbot, selected_db_state, main_config_state]
        send_btn.click(fn=run_chat, inputs=chat_inputs, outputs=[chatbot]).then(fn=lambda: gr.update(value=""), inputs=None, outputs=[chat_input])
        chat_input.submit(fn=run_chat, inputs=chat_inputs, outputs=[chatbot]).then(fn=lambda: gr.update(value=""), inputs=None, outputs=[chat_input])
        
        return demo