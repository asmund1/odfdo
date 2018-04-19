#!/usr/bin/env python
"""
Transpose a table. Create a spreadsheet table (example: 50 rows and 20
columns), and subsequently create a new table in a separate sheet where the
columns and rows are now swapped (e.g. 20 rows and 50 columns).
"""
import os

from odfdo import Document, Table, Row

if __name__ == "__main__":
    spreadsheet = Document('spreadsheet')

    # Populate the table in the spreadsheet
    body = spreadsheet.body
    table = Table("Table")
    body.append(table)

    lines = 50
    cols = 20

    for line in range(lines):
        row = Row()
        for column in range(cols):
            row.set_value(column, "%s%s" % (chr(65 + column), line + 1))
        table.append(row)

    print("Size of Table :", table.size)

    table2 = Table("Symetry")

    # building the symetric table using classical method :
    for x in range(cols):
        values = table.get_column_values(x)
        table2.set_row_values(x, values)
    body.append(table2)

    print("Size of symetric table 2 :", table2.size)

    # a more simple solution with the table.transpose() method :
    table3 = table.clone
    table3.transpose()
    table3.name = "Transpose"
    body.append(table3)

    print("Size of symetric table 3 :", table3.size)

    if not os.path.exists('test_output'):
        os.mkdir('test_output')

    output = os.path.join('test_output', "my_transposed_spreadsheet.ods")

    spreadsheet.save(target=output, pretty=True)
