import dearpygui.dearpygui as dpg

dpg.create_context()

with dpg.window(label="Tutorial",width=350,height=350,no_scrollbar=True):
    # add 6*6 buttons that resize to be together everytime the window is resized:

    buttonWidth = 50
    buttonHeight = 50

    # get window size:
    

    for i in range(6):
        with dpg.group(horizontal=True):
            for j in range(6):
                dpg.add_button(label=" ", width=buttonWidth, height=buttonHeight)

dpg.create_viewport(title="Checkers With Roman and Yigit", width=800, height=800)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()