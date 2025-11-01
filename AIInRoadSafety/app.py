from flask import Flask, render_template, request, send_file
import pandas as pd
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    table_data = None

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.pdf'):
            try:
                reader = PdfReader(file)
                data = []

                # Extract text page by page
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    # Trim long text for table preview
                    short_text = text[:200].replace('\n', ' ') + ("..." if len(text) > 200 else "")
                    data.append({"Page": i + 1, "Content": short_text})

                # Create dataframe and save for export
                df = pd.DataFrame(data)
                df.to_csv('extracted_pdf_data.csv', index=False)
                table_data = df.to_html(classes='data-table', index=False)

            except Exception as e:
                return render_template('index.html', table_data=None, error=f"Error reading PDF: {e}")
        else:
            return render_template('index.html', table_data=None, error="Please upload a valid PDF file.")

    return render_template('index.html', table_data=table_data, error=None)


@app.route('/export', methods=['GET'])
def export_pdf():
    try:
        df = pd.read_csv('extracted_pdf_data.csv')

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, height - 50, "Extracted PDF Report")

        pdf.setFont("Helvetica", 10)
        y = height - 100
        for _, row in df.iterrows():
            line = f"Page {row['Page']}: {row['Content']}"
            pdf.drawString(50, y, line[:120])  # Limit line width
            y -= 20
            if y < 50:
                pdf.showPage()
                y = height - 50

        pdf.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="Extracted_Report.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return f"Error generating PDF: {e}", 500


@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)