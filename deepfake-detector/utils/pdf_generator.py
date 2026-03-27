"""
PDF Report Generator for DeepFake Detection Results
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
import io
import base64


class PDFReportGenerator:
    """Generate professional PDF reports for deepfake detection results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='ResultStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='ConfidenceStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=5
        ))
    
    def generate_report(self, result, output_path=None):
        """
        Generate PDF report for a single analysis result
        Returns the PDF file path or bytes
        """
        if output_path is None:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Story (content) list
        story = []
        
        # Title
        story.append(Paragraph("DeepFake Detection Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Result Summary
        self.add_result_summary(story, result)
        
        # File Information
        self.add_file_info(story, result)
        
        # Detection Details
        self.add_detection_details(story, result)
        
        # Model Scores
        if result.get('scores'):
            self.add_model_scores(story, result['scores'])
        
        # Confidence Meter Visualization
        self.add_confidence_meter(story, result)
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            f"Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
            self.styles['Italic']
        ))
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def add_result_summary(self, story, result):
        """Add result summary section"""
        is_fake = result.get('is_fake', False)
        
        story.append(Paragraph("Analysis Result", self.styles['CustomHeading']))
        
        # Result table
        data = [
            ["Status", "⚠️ DEEPFAKE DETECTED" if is_fake else "✅ AUTHENTIC MEDIA"],
            ["Confidence", f"{result.get('confidence', 0)*100:.1f}%"],
            ["Probability", f"{result.get('probability', 0)*100:.1f}%"],
            ["Detection Method", result.get('model_used', 'Ensemble')]
        ]
        
        table = Table(data, colWidths=[120, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    def add_file_info(self, story, result):
        """Add file information section"""
        story.append(Paragraph("File Information", self.styles['CustomHeading']))
        
        file_info = result.get('file_info', {})
        media_type = result.get('media_type', 'image')
        
        data = [
            ["Filename", result.get('filename', 'Unknown')],
            ["Media Type", media_type.capitalize()],
            ["File Size", f"{file_info.get('size_mb', 'N/A')} MB"],
            ["Analysis Time", result.get('analysis_time', 'Unknown')[:19].replace('T', ' ')]
        ]
        
        if media_type == 'video':
            data.append(["Frames Analyzed", str(result.get('frames_analyzed', 'N/A'))])
            data.append(["Consistency", f"{result.get('consistency', 0)*100:.1f}%"])
        
        table = Table(data, colWidths=[120, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    def add_detection_details(self, story, result):
        """Add detection details section"""
        story.append(Paragraph("Detection Analysis", self.styles['CustomHeading']))
        
        if result.get('reasoning'):
            story.append(Paragraph(f"<b>Reasoning:</b> {result['reasoning']}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        if result.get('detailed_features'):
            features = result['detailed_features']
            story.append(Paragraph("Feature Analysis:", self.styles['ResultStyle']))
            
            data = []
            if 'texture_variance' in features:
                texture_score = features.get('fake_texture_score', 0) * 100
                data.append(["Texture Analysis", f"{texture_score:.1f}%", "Higher = smoother (fake indicator)"])
            
            if 'edge_density' in features:
                edge_score = features.get('fake_edge_score', 0) * 100
                data.append(["Edge Pattern", f"{edge_score:.1f}%", "Higher = inconsistent edges"])
            
            if 'noise_level' in features:
                noise_score = features.get('fake_noise_score', 0) * 100
                data.append(["Noise Pattern", f"{noise_score:.1f}%", "Higher = unnatural noise"])
            
            if data:
                table = Table(data, colWidths=[120, 80, 220])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
                ]))
                story.append(table)
    
    def add_model_scores(self, story, scores):
        """Add model scores section"""
        story.append(Paragraph("Model Scores", self.styles['CustomHeading']))
        
        data = [["Model", "Score", "Interpretation"]]
        for model, score in scores.items():
            model_name = model.capitalize()
            score_percent = score * 100
            interpretation = "Indicates fake" if score > 0.5 else "Indicates real"
            data.append([model_name, f"{score_percent:.1f}%", interpretation])
        
        table = Table(data, colWidths=[100, 80, 240])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
    
    def add_confidence_meter(self, story, result):
        """Add confidence meter visualization"""
        story.append(Paragraph("Confidence Analysis", self.styles['CustomHeading']))
        
        confidence = result.get('confidence', 0) * 100
        is_fake = result.get('is_fake', False)
        
        # Create drawing for confidence meter
        drawing = Drawing(400, 50)
        
        # Background bar
        drawing.add(Rect(0, 20, 400, 20, fillColor=colors.HexColor('#e5e7eb'), strokeColor=None))
        
        # Fill bar
        fill_width = (confidence / 100) * 400
        fill_color = colors.HexColor('#ef4444') if is_fake else colors.HexColor('#10b981')
        drawing.add(Rect(0, 20, fill_width, 20, fillColor=fill_color, strokeColor=None))
        
        # Threshold line at 50%
        drawing.add(Rect(200, 15, 2, 30, fillColor=colors.HexColor('#1f2937'), strokeColor=None))
        
        # Add text
        confidence_text = f"{confidence:.1f}% Confidence"
        drawing.add(String(200, 0, confidence_text, fontSize=10, textAnchor='middle'))
        
        story.append(drawing)
        story.append(Spacer(1, 10))


def generate_pdf_report(result):
    """Helper function to generate PDF report"""
    generator = PDFReportGenerator()
    return generator.generate_report(result)