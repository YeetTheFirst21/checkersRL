import dearpygui.dearpygui as dpg

def save_callback():
    print("Save Clicked")

dpg.create_context()
dpg.create_viewport(title="Checkers With Roman and Yigit", width=800, height=800)
dpg.setup_dearpygui()

with dpg.window(label="MainCheckers", width=400, height=400, no_collapse=True,no_scrollbar=True):
    with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit, resizable=False, no_host_extendX=True,
                   borders_innerV=True, borders_outerV=True, borders_outerH=True):
        # creating the squared grid of the 6*6 checkers board:
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()

        for i in range(6):
            with dpg.table_row():
                for j in range(6):
                    dpg.add_button(label=" ", width=50, height=50)

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()