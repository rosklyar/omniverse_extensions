import omni.ext
import carb.events
import omni.kit.app
import omni.ui as ui
import omni.kit.window.filepicker as fp
from pxr import Usd, UsdGeom, Gf
import omni.usd
import os
from os.path import exists
import asyncio
import json

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    def on_startup(self, ext_id):
        
        async def export_eyedarts():
            output_folder = "C:/Users/rskliar/ue-projects/test_folder"              
            progress_window = ui.Window("Export eye darts to json...", width=750, height=100)
            with progress_window.frame:
                with ui.VStack():
                    file_label = ui.StringField()
                    pb = ui.ProgressBar()
                    pb.model.set_value(0)


            stage = omni.usd.get_context().get_stage()
            manager = omni.audio2face.player.get_ext().player_manager()
            instance = manager.get_instance("/World/LazyGraph/Player")
            l_eye = stage.GetPrimAtPath("/World/male_fullface/char_male_model_hi/l_eye_grp_hi")
            r_eye = stage.GetPrimAtPath("/World/male_fullface/char_male_model_hi/r_eye_grp_hi")
            wav_files_folder = instance.get_abs_track_root_path()
            files_to_process = getWavFiles(wav_files_folder)
            for f in files_to_process:
                instance.set_track_name(f)
                pb.model.set_value(0)
                print("Processing file:" + f)
                file_label.model.set_value(f)
                fileLengthInSeconds = instance.get_range_end()
                time = 0.0
                result = []
                while(time < fileLengthInSeconds):
                    e = await omni.kit.app.get_app().next_update_async()
                    time += 1.0 / 60
                    instance.set_time(time)
                    pose_l = omni.usd.utils.get_world_transform_matrix(l_eye)
                    pose_r = omni.usd.utils.get_world_transform_matrix(r_eye)
                    l_rx, l_ry, l_rz = pose_l.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                    r_rx, r_ry, r_rz = pose_r.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                    frame = [l_rx, l_ry, l_rz, r_rx, r_ry, r_rz]
                    result.append(frame)
                    pb.model.set_value(time / fileLengthInSeconds)
                result_json = {
                    "numPoses": 6,
                    "numFrames": len(result),
                    "facsNames" : ["l_rx", "l_ry", "l_rz", "r_rx", "r_ry", "r_rz"],
                    "weightMat": result
                }
                with open(output_folder + "/" + f[:-3] + "json", 'w') as outfile:
                    json.dump(result_json, outfile)
            
            progress_window.destroy()
            progress_window.visible = False

        def on_change(event):
            if(event.type == 8):
                asyncio.ensure_future(export_eyedarts())
            pass

        print("[playtika.eyedarts.export] ExportEyeDarts startup")
        self.output_folder = ""
        self.fps = 60
        self._window = ui.Window("Export eye darts", width=750, height=300)
        self.filePicker = None
        self.folder_label = None
        print("Stream=" + str(omni.kit.app.get_app().get_message_bus_event_stream()))
        print("Update Stream=" + str(omni.kit.app.get_app().get_update_event_stream()))
        self._subscription = omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(on_change)
        print("[playtika.eyedarts.export] ExportEyeDarts subscription created")
        with self._window.frame:
            with ui.VStack():

                def getWavFiles(json_files_folder):
                    files = []
                    if json_files_folder and not exists(json_files_folder):
                        raise Exception("Please, select existed folder with JSON files!")
                    for file in os.listdir(json_files_folder):
                        if file.endswith('.wav'):
                            files.append(file)
                    return files

                def on_combobox_changed(model, item):
                    self.fps = model.get_item_value_model(model.get_item_children()[model.get_item_value_model().as_int]).as_int

                def on_click():
                    asyncio.ensure_future(export())
                
                async def export():
                    
                    progress_window = ui.Window("Export eye darts to json...", width=750, height=100)
                    with progress_window.frame:
                        with ui.VStack():
                            file_label = ui.StringField()
                            pb = ui.ProgressBar()
                            pb.model.set_value(0)

                    if(self.output_folder):

                        stage = omni.usd.get_context().get_stage()
                        manager = omni.audio2face.player.get_ext().player_manager()
                        instance = manager.get_instance("/World/LazyGraph/Player")
                        l_eye = stage.GetPrimAtPath("/World/male_fullface/char_male_model_hi/l_eye_grp_hi")
                        r_eye = stage.GetPrimAtPath("/World/male_fullface/char_male_model_hi/r_eye_grp_hi")
                        wav_files_folder = instance.get_abs_track_root_path()
                        files_to_process = getWavFiles(wav_files_folder)
                        for f in files_to_process:
                            instance.set_track_name(f)
                            pb.model.set_value(0)
                            print("Processing file:" + f)
                            file_label.model.set_value(f)
                            fileLengthInSeconds = instance.get_range_end()
                            time = 0.0
                            result = []
                            while(time < fileLengthInSeconds):
                                e = await omni.kit.app.get_app().next_update_async()
                                time += 1.0 / self.fps
                                instance.set_time(time)
                                pose_l = omni.usd.utils.get_world_transform_matrix(l_eye)
                                pose_r = omni.usd.utils.get_world_transform_matrix(r_eye)
                                l_rx, l_ry, l_rz = pose_l.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                                r_rx, r_ry, r_rz = pose_r.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                                frame = [l_rx, l_ry, l_rz, r_rx, r_ry, r_rz]
                                result.append(frame)
                                pb.model.set_value(time / fileLengthInSeconds)
                            result_json = {
                                "numPoses": 6,
                                "numFrames": len(result),
                                "facsNames" : ["l_rx", "l_ry", "l_rz", "r_rx", "r_ry", "r_rz"],
                                "weightMat": result
                            }
                            with open(self.output_folder + "/" + f[:-3] + "json", 'w') as outfile:
                                json.dump(result_json, outfile)
                    
                    progress_window.destroy()
                    progress_window.visible = False

                def on_click_open(file_name, dir_name):
                    print("File name: " + dir_name)
                    self.output_folder = dir_name
                    self.folder_label.text = "Output folder: " + self.output_folder
                    self.filePicker.hide()
                
                def show_file_picker():
                    print("show file picker")
                    self.filePicker = fp.FilePickerDialog("Select output folder", apply_button_label="Select", click_apply_handler=on_click_open)
                    self.filePicker.show()
                with ui.HStack():
                    self.folder_label = ui.Label("Output folder: " + self.output_folder, height=20)
                    ui.Button("Select", clicked_fn=lambda: show_file_picker(), width = 20, height=20)
                with ui.HStack():
                    ui.Label("FPS: ", height=20)
                    fpsCombobox = ui.ComboBox(0, "60", "24")
                    fpsCombobox.model.add_item_changed_fn(lambda model, item: on_combobox_changed(model, item))
                ui.Button("Export", clicked_fn=lambda: on_click())

    def on_shutdown(self):
        print("[playtika.eyedarts.export] ExportEyeDarts shutdown")
    
def getWavFiles(json_files_folder):
    files = []
    if json_files_folder and not exists(json_files_folder):
        raise Exception("Please, select existed folder with JSON files!")
    for file in os.listdir(json_files_folder):
        if file.endswith('.wav'):
            files.append(file)
    return files
