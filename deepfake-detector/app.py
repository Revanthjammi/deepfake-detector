"""
Main Flask application for DeepFake Detection System
Complete Working Version with History, PDF Export, and Image/Video Thumbnails
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import json
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np

# Import config
from config import UPLOAD_FOLDER, RESULTS_FOLDER, THUMBNAILS_FOLDER, ALLOWED_EXTENSIONS, MAX_FILE_SIZE

# Import detector
from models.detector import detector

# Import utils
from utils.result_saver import save_result, load_results

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'deepfake-detector-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Max 200MB
CORS(app)

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS.get(file_type, set())


def create_thumbnail(file_path, media_type):
    """Create thumbnail for image or video - SAVES TO PERMANENT LOCATION"""
    try:
        thumbnail_path = None
        
        # Ensure thumbnails folder exists
        os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)
        
        if media_type == 'image':
            # For images, use the image itself as thumbnail
            img = cv2.imread(file_path)
            if img is not None:
                # Resize to reasonable size
                height, width = img.shape[:2]
                max_size = 500
                if width > max_size:
                    ratio = max_size / width
                    new_width = max_size
                    new_height = int(height * ratio)
                    img = cv2.resize(img, (new_width, new_height))
                
                # Save thumbnail to PERMANENT location
                thumb_filename = f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                thumbnail_path = os.path.join(THUMBNAILS_FOLDER, thumb_filename)
                cv2.imwrite(thumbnail_path, img)
                print(f"✅ Image thumbnail created: {thumbnail_path}")
                return thumbnail_path
            else:
                print(f"❌ Could not read image: {file_path}")
                
        elif media_type == 'video':
            # For videos, extract first frame
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret and frame is not None:
                # Resize
                height, width = frame.shape[:2]
                max_size = 500
                if width > max_size:
                    ratio = max_size / width
                    new_width = max_size
                    new_height = int(height * ratio)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Save thumbnail to PERMANENT location
                thumb_filename = f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                thumbnail_path = os.path.join(THUMBNAILS_FOLDER, thumb_filename)
                cv2.imwrite(thumbnail_path, frame)
                print(f"✅ Video thumbnail created: {thumbnail_path}")
            else:
                print(f"❌ Could not extract frame from video: {file_path}")
            cap.release()
            return thumbnail_path
            
    except Exception as e:
        print(f"❌ Error creating thumbnail: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_pdf_report(data):
    """Generate PDF report with thumbnail - FIXED VERSION"""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import inch
        from PIL import Image as PILImage
        import tempfile
        
        # Create buffer for PDF
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        content = []
        
        # Title
        content.append(Paragraph("DeepFake Detection Report", styles['CustomTitle']))
        content.append(Spacer(1, 20))
        
        # Result Summary
        is_fake = data.get('label') == 'FAKE'
        result_text = "⚠️ DEEPFAKE DETECTED" if is_fake else "✅ AUTHENTIC MEDIA"
        
        result_style = ParagraphStyle(
            name='ResultStyle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#ef4444') if is_fake else colors.HexColor('#10b981'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        content.append(Paragraph(result_text, result_style))
        content.append(Spacer(1, 10))
        
        # ==========================================================
        # ADD IMAGE/VIDEO THUMBNAIL TO PDF - FIXED VERSION
        # ==========================================================
        
        thumbnail_path = data.get('thumbnail_path')
        media_type = data.get('media_type', 'image')
        
        print(f"📸 Looking for thumbnail at: {thumbnail_path}")
        
        # Check if thumbnail exists
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                # Load and resize image for PDF - DIRECTLY FROM PERMANENT FILE
                img = PILImage.open(thumbnail_path)
                print(f"✅ Thumbnail loaded: {thumbnail_path}")
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate dimensions for PDF (max width 5 inches, maintain aspect ratio)
                max_width = 5 * inch
                max_height = 4 * inch
                
                img_width, img_height = img.size
                aspect = img_height / img_width
                
                if img_width > max_width:
                    img_width = max_width
                    img_height = img_width * aspect
                
                if img_height > max_height:
                    img_height = max_height
                    img_width = img_height / aspect
                
                # Create a BytesIO buffer for the image - NO TEMP FILE
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=85)
                img_buffer.seek(0)
                
                # Add image to PDF directly from buffer
                pdf_img = ReportLabImage(img_buffer, width=img_width, height=img_height)
                pdf_img.hAlign = 'CENTER'
                content.append(pdf_img)
                content.append(Spacer(1, 10))
                
                # Add caption
                caption_style = ParagraphStyle(
                    name='Caption',
                    parent=styles['Italic'],
                    fontSize=10,
                    textColor=colors.HexColor('#64748b'),
                    alignment=TA_CENTER
                )
                
                if media_type == 'video':
                    caption_text = "Video Thumbnail (First Frame)"
                else:
                    caption_text = "Analyzed Image"
                
                content.append(Paragraph(caption_text, caption_style))
                content.append(Spacer(1, 20))
                
            except Exception as e:
                print(f"❌ Error adding thumbnail to PDF: {e}")
                import traceback
                traceback.print_exc()
                content.append(Paragraph(f"⚠️ Thumbnail could not be loaded", styles['Italic']))
                content.append(Spacer(1, 20))
        else:
            # Add placeholder
            placeholder_style = ParagraphStyle(
                name='Placeholder',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#94a3b8'),
                alignment=TA_CENTER,
                backColor=colors.HexColor('#f1f5f9'),
                borderPadding=20
            )
            
            missing_reason = ""
            if not thumbnail_path:
                missing_reason = " (no thumbnail path)"
            elif not os.path.exists(thumbnail_path):
                missing_reason = f" (file not found: {os.path.basename(thumbnail_path)})"
            
            content.append(Paragraph(f"[{media_type.upper()} Preview Not Available{missing_reason}]", placeholder_style))
            content.append(Spacer(1, 20))
            print(f"⚠️ Thumbnail not available: {thumbnail_path}")
        
        # ==========================================================
        # FILE INFORMATION
        # ==========================================================
        
        content.append(Paragraph("Analysis Details", styles['CustomHeading']))
        
        # File Information Table
        file_info_data = [
            ["Filename", data.get('filename', 'Unknown')],
            ["Media Type", media_type.capitalize()],
            ["Analysis Time", data.get('analysis_time', 'Unknown')[:19].replace('T', ' ')],
            ["Confidence", f"{data.get('confidence', 0)*100:.1f}%"],
            ["Probability", f"{data.get('probability', 0)*100:.1f}%"],
            ["Model Used", data.get('model_used', 'Ensemble')]
        ]
        
        # Add video-specific info if applicable
        if media_type == 'video' and data.get('frames_analyzed'):
            file_info_data.append(["Frames Analyzed", str(data.get('frames_analyzed', 'N/A'))])
            if data.get('consistency'):
                file_info_data.append(["Consistency", f"{data.get('consistency', 0)*100:.1f}%"])
        
        table = Table(file_info_data, colWidths=[120, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        content.append(table)
        content.append(Spacer(1, 20))
        
        # ==========================================================
        # MODEL SCORES
        # ==========================================================
        
        if data.get('scores'):
            content.append(Paragraph("Model Scores", styles['CustomHeading']))
            
            scores_data = [["Model", "Score", "Interpretation"]]
            for model, score in data['scores'].items():
                model_name = model.capitalize()
                score_percent = score * 100
                interpretation = "⚠️ Indicates fake" if score > 0.5 else "✅ Indicates real"
                scores_data.append([model_name, f"{score_percent:.1f}%", interpretation])
            
            scores_table = Table(scores_data, colWidths=[100, 80, 200])
            scores_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
            ]))
            
            content.append(scores_table)
            content.append(Spacer(1, 20))
        
        # ==========================================================
        # ANALYSIS REASONING
        # ==========================================================
        
        if data.get('reasoning'):
            content.append(Paragraph("Analysis Reasoning", styles['CustomHeading']))
            
            reasoning_style = ParagraphStyle(
                name='Reasoning',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#334155'),
                backColor=colors.HexColor('#f8fafc'),
                borderPadding=10,
                spaceAfter=10
            )
            content.append(Paragraph(data['reasoning'], reasoning_style))
            content.append(Spacer(1, 20))
        
        # ==========================================================
        # FOOTER
        # ==========================================================
        
        content.append(Spacer(1, 40))
        content.append(Paragraph(
            f"Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
            styles['Italic']
        ))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        raise e


# ==========================================================
# ROUTES
# ==========================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')


@app.route('/history')
def history():
    """History page showing all analyses"""
    return render_template('history.html')


@app.route('/result/<result_id>')
def view_result(result_id):
    """View detailed analysis result"""
    # Load all results
    results = load_results(100)
    
    # Find the specific result
    result = None
    for r in results:
        if r.get('result_id') == result_id:
            result = r
            break
    
    if not result:
        return render_template('404.html'), 404
    
    return render_template('result.html', result=result)


@app.route('/api/status')
def status():
    """Health check endpoint"""
    models_loaded = 0
    device = "cpu"
    
    try:
        if hasattr(detector, 'model_manager') and detector.model_manager:
            if hasattr(detector.model_manager, 'model') and detector.model_manager.model:
                models_loaded = 1
    except:
        pass
    
    try:
        if hasattr(detector, 'device'):
            device = detector.device
    except:
        pass
    
    return jsonify({
        'status': 'running',
        'models_loaded': models_loaded,
        'device': device,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/results')
def get_results():
    """Get recent analysis results"""
    limit = request.args.get('limit', 50, type=int)
    results = load_results(limit)
    return jsonify({'results': results, 'count': len(results)})


@app.route('/api/result/<result_id>')
def get_single_result(result_id):
    """Get single analysis result by ID"""
    results = load_results(100)
    for result in results:
        if result.get('result_id') == result_id:
            return jsonify(result)
    return jsonify({'error': 'Result not found'}), 404


@app.route('/api/export-pdf/<result_id>')
def export_pdf(result_id):
    """Export analysis result as PDF"""
    results = load_results(100)
    
    result = None
    for r in results:
        if r.get('result_id') == result_id:
            result = r
            break
    
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    try:
        pdf_data = {
            'filename': result.get('filename', 'Unknown'),
            'label': 'FAKE' if result.get('is_fake') else 'REAL',
            'probability': result.get('probability', 0),
            'confidence': result.get('confidence', 0),
            'media_type': result.get('media_type', 'image'),
            'model_used': result.get('model_used', 'Ensemble'),
            'analysis_time': result.get('analysis_time', datetime.now().isoformat()),
            'scores': result.get('scores', {}),
            'reasoning': result.get('reasoning', 'Analysis completed'),
            'thumbnail_path': result.get('thumbnail_path'),
            'frames_analyzed': result.get('frames_analyzed'),
            'consistency': result.get('consistency')
        }
        
        pdf_buffer = generate_pdf_report(pdf_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"deepfake_report_{result_id}.pdf"
        )
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500


@app.route('/api/export-json/<result_id>')
def export_json(result_id):
    """Export analysis result as JSON"""
    results = load_results(100)
    
    for r in results:
        if r.get('result_id') == result_id:
            json_data = json.dumps(r, indent=2)
            return send_file(
                io.BytesIO(json_data.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'deepfake_report_{result_id}.json'
            )
    
    return jsonify({'error': 'Result not found'}), 404


@app.route('/api/export-csv/<result_id>')
def export_csv(result_id):
    """Export analysis result as CSV"""
    results = load_results(100)
    
    for r in results:
        if r.get('result_id') == result_id:
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Field', 'Value'])
            writer.writerow(['Filename', r.get('filename', 'Unknown')])
            writer.writerow(['Result', 'FAKE' if r.get('is_fake') else 'REAL'])
            writer.writerow(['Probability', f"{r.get('probability', 0)*100:.1f}%"])
            writer.writerow(['Confidence', f"{r.get('confidence', 0)*100:.1f}%"])
            writer.writerow(['Media Type', r.get('media_type', 'image')])
            writer.writerow(['Analysis Time', r.get('analysis_time', 'Unknown')])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'deepfake_report_{result_id}.csv'
            )
    
    return jsonify({'error': 'Result not found'}), 404


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if file_ext in ALLOWED_EXTENSIONS['image']:
        file_type = 'image'
    elif file_ext in ALLOWED_EXTENSIONS['video']:
        file_type = 'video'
    else:
        return jsonify({'error': f'Unsupported file type: {file_ext}'}), 400

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE[file_type]:
        return jsonify({
            'error': f'File too large. Max {MAX_FILE_SIZE[file_type] // (1024 * 1024)}MB'
        }), 400

    temp_filename = f"{uuid.uuid4().hex}_{filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    file.save(temp_path)
    
    print(f"📁 File saved: {temp_path}")

    try:
        thumbnail_path = create_thumbnail(temp_path, file_type)
        print(f"🖼️ Thumbnail created: {thumbnail_path}")
        
        if file_type == 'image':
            result = detector.detect_image(temp_path)
        else:
            result = detector.detect_video(temp_path)

        result['file_info'] = {
            'filename': filename,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'type': file_type
        }
        
        result['thumbnail_path'] = thumbnail_path
        result['media_type'] = file_type

        if 'result_id' not in result:
            result['result_id'] = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        save_result(result)

        return jsonify(result)

    except Exception as e:
        print(f"❌ Error in analyze: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"🗑️ Temp file removed: {temp_path}")
        except Exception as e:
            print(f"⚠️ Could not remove temp file: {e}")


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF report from current result"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        pdf_buffer = generate_pdf_report(data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{data.get('filename', 'report').replace('.', '_')}_report.pdf"
        )
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500


@app.route('/api/stats')
def get_stats():
    """Get statistics for dashboard"""
    results = load_results(1000)
    
    total = len(results)
    fake_count = sum(1 for r in results if r.get('is_fake'))
    real_count = total - fake_count
    avg_confidence = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
    
    daily_stats = {}
    for result in results:
        date = result.get('analysis_time', '')[:10]
        if date:
            if date not in daily_stats:
                daily_stats[date] = {'fake': 0, 'real': 0}
            if result.get('is_fake'):
                daily_stats[date]['fake'] += 1
            else:
                daily_stats[date]['real'] += 1
    
    return jsonify({
        'total_analyses': total,
        'fake_count': fake_count,
        'real_count': real_count,
        'avg_confidence': avg_confidence,
        'daily_stats': daily_stats
    })


@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500 error handler"""
    return jsonify({'error': 'Internal server error'}), 500


# ==========================================================
# RUN APP
# ==========================================================
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🛡️ DEEPFAKE DETECTOR - COMPLETE VERSION")
    print("="*70)
    
    models_loaded = 0
    device = "CPU"
    
    try:
        if hasattr(detector, 'model_manager') and detector.model_manager:
            if hasattr(detector.model_manager, 'model') and detector.model_manager.model:
                models_loaded = 1
    except:
        models_loaded = 0
    
    try:
        if hasattr(detector, 'device'):
            device = detector.device.upper()
    except:
        device = "CPU"
    
    print(f"Models loaded: {models_loaded}")
    print(f"Device: {device}")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Results folder: {RESULTS_FOLDER}")
    print(f"Thumbnails folder: {THUMBNAILS_FOLDER}")
    print("="*70)
    print("🌐 Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)