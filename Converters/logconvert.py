import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone
import pandas as pd


def custom_parse_can_log_entry(log_entry):
    parts = log_entry.strip().split(' ')
    
    if len(parts) >= 3:
        try:
            timestamp = float(parts[0][1:-1])  # Extract timestamp without parentheses
            interface = parts[1]
            message_data = parts[2].split('#')
            
            if len(message_data) == 2:
                message_id, data_hex = message_data
                data_bytes = bytes.fromhex(data_hex)
                
                # Handle single-byte and multi-byte data explicitly
                values = list(data_bytes)
                
                return {
                    'timestamp': timestamp,
                    'interface': interface,
                    'message_id': "0x"+message_id,  # Keep message ID as a hexadecimal string
                    'values': values
                }
        except (ValueError, IndexError):
            pass
    
    return None


class CanLogViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Log Viewer")

        # Create a treeview for displaying the data in a table
        self.tree = ttk.Treeview(root, columns=('Timestamp', 'Interface', 'Message ID', 'Values', 'Readable Values'))
        self.tree.heading('Timestamp', text='Timestamp')
        self.tree.heading('Interface', text='Interface')
        self.tree.heading('Message ID', text='Frame ID')
        self.tree.heading('Values', text='Converted Values')
        self.tree.heading('Readable Values', text='Original Values')

        self.tree.pack(expand=True, fill='both')  # Expand to fill available space

        # Parse the CAN dump log and populate the table
        self.log_file_path = self.ask_for_log_file()
        if self.log_file_path:
            self.root.title(f"CAN Log Viewer - {self.log_file_path}")
            self.populate_table()
            self.adjust_column_widths()

        # Export to spreadsheet button
        export_button = tk.Button(root, text="Export to Excel", command=self.export_to_excel)
        export_button.pack(pady=10)

    def ask_for_log_file(self):
        # Ask user for the log file path using filedialog
        log_file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        return log_file_path

    def convert_epoch_to_datetime(self, epoch_time):
        # Convert epoch time to a human-readable format
        datetime_obj = datetime.fromtimestamp(epoch_time, timezone.utc)
        formatted_datetime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_datetime

    def populate_table(self):
        parsed_data = [custom_parse_can_log_entry(line) for line in open(self.log_file_path, 'r') if line.strip()]

        for entry in parsed_data:
            # Convert epoch time to a human-readable format
            timestamp_str = self.convert_epoch_to_datetime(entry['timestamp'])

            # Handle single-byte and multi-byte values for display
            if len(entry['values']) == 1:
                values_str = str(entry['values'][0])
            else:
                values_str = ', '.join(map(str, entry['values']))

            # Add a new column for readable values
            readable_values_str = ', '.join(map(lambda x: f"{x:02X}", entry['values']))

            # Insert data into the treeview without 'Entry #' column
            self.tree.insert('', 'end', values=(timestamp_str, entry['interface'], entry['message_id'], values_str, readable_values_str))

    def adjust_column_widths(self):
        # Adjust column widths based on content
        for col in self.tree['columns']:
            header_width = len(col)
            data_width = max(len(str(self.tree.set(item, col))) for item in self.tree.get_children())
            max_width = max(header_width, data_width)
            self.tree.column(col, width=max_width + 10)  # Add padding for better appearance

    def export_to_excel(self):
        # Get data from the treeview
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            data.append(list(values))

        # Create a DataFrame
        df = pd.DataFrame(data, columns=['Timestamp', 'Interface', 'Frame ID', 'Converted Values', 'Original Values'])

        # Ask user for the output file path using filedialog
        output_file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if output_file_path:
            # Export DataFrame to Excel
            df.to_excel(output_file_path, index=False)
            messagebox.showinfo("Export Successful", f"Data exported to {output_file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    viewer = CanLogViewer(root)
    root.mainloop()
