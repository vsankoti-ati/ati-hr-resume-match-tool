"""
Report Generator Module
Generates PDF reports for resume match analysis
"""
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import logging

from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_candidate_name_from_filename(filename: str) -> str:
    """Extract and sanitize candidate name from profile filename"""
    name = Path(filename).stem
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    return name[:50] if len(name) > 50 else name or "Candidate"


class ReportGenerator:
    """Generator for PDF reports"""
    
    def __init__(self, page_size=letter):
        """
        Initialize report generator
        
        Args:
            page_size: Page size for PDF (default: letter)
        """
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style (reduced by 10%)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1f497d'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style (reduced by 10%)
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f497d'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subheading style (reduced by 10%)
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#4472c4'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style (reduced by 10%)
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))
        
        # Table cell style (reduced by 10%)
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['BodyText'],
            fontSize=8,
            alignment=TA_LEFT,
            leading=10,
            spaceAfter=0,
            spaceBefore=0
        ))
    
    def _create_table_cell(self, text: str, style_name: str = 'TableCell') -> Paragraph:
        """
        Create a table cell with word wrapping
        
        Args:
            text: Text content for the cell
            style_name: Style to apply
            
        Returns:
            Paragraph object with wrapped text
        """
        if not text or text == 'N/A':
            return Paragraph(text or 'N/A', self.styles[style_name])
        
        # Escape special XML characters for reportlab
        text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return Paragraph(text, self.styles[style_name])
    
    def _get_match_color(self, percentage: float) -> colors.Color:
        """
        Get color based on match percentage
        
        Args:
            percentage: Match percentage (0-100)
            
        Returns:
            Color object
        """
        if percentage >= Config.MATCH_THRESHOLD_EXCELLENT:
            return colors.HexColor('#28a745')  # Green
        elif percentage >= Config.MATCH_THRESHOLD_GOOD:
            return colors.HexColor('#ffc107')  # Yellow
        elif percentage >= Config.MATCH_THRESHOLD_FAIR:
            return colors.HexColor('#fd7e14')  # Orange
        else:
            return colors.HexColor('#dc3545')  # Red
    
    def _create_header(self, analysis_data: Dict[str, Any]) -> list:
        """Create report header section"""
        elements = []
        
        # Title
        title = Paragraph(Config.REPORT_TITLE, self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Extract candidate name from metadata
        metadata_dict = analysis_data.get('metadata', {})
        profile_filename = metadata_dict.get('profile_filename', 'Candidate')
        candidate_name = get_candidate_name_from_filename(profile_filename)
        
        # Metadata table
        metadata = [
            ['Name:', candidate_name],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Analysis Tool:', Config.REPORT_AUTHOR]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_overall_match_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create overall match percentage section"""
        elements = []
        
        # Section heading
        heading = Paragraph("Overall Match Score", self.styles['CustomHeading'])
        elements.append(heading)
        
        # Match percentage (no border, reduced font size)
        percentage = analysis_data.get('overall_match_percentage', 0)
        match_color = self._get_match_color(percentage)
        
        match_data = [[
            Paragraph(f"<font size=28 color={match_color.hexval()}><b>{percentage}%</b></font>",
                     self.styles['CustomBody'])
        ]]
        
        match_table = Table(match_data, colWidths=[6*inch])
        match_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        elements.append(match_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Summary
        summary = analysis_data.get('match_summary', 'No summary available')
        summary_para = Paragraph(summary, self.styles['CustomBody'])
        elements.append(summary_para)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_matching_skills_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create matching skills section as a 4-column table"""
        elements = []
        
        heading = Paragraph("Matching Skills & Qualifications", self.styles['CustomHeading'])
        elements.append(heading)
        
        matching_skills = analysis_data.get('matching_skills', {})
        
        # Prepare data for 4-column table
        technical_skills = matching_skills.get('technical_skills', [])
        soft_skills = matching_skills.get('soft_skills', [])
        qualifications = matching_skills.get('qualifications', [])
        experience_areas = matching_skills.get('experience_areas', [])
        
        # Create bullet list strings for each column
        def format_list(items):
            if not items:
                return "None"
            return '<br/>'.join([f"• {item}" for item in items])
        
        # Build table data
        table_data = [
            # Header row
            [
                Paragraph('<b>Technical Skills</b>', self.styles['TableCell']),
                Paragraph('<b>Soft Skills</b>', self.styles['TableCell']),
                Paragraph('<b>Qualifications</b>', self.styles['TableCell']),
                Paragraph('<b>Experience Areas</b>', self.styles['TableCell'])
            ],
            # Data row
            [
                Paragraph(format_list(technical_skills), self.styles['TableCell']),
                Paragraph(format_list(soft_skills), self.styles['TableCell']),
                Paragraph(format_list(qualifications), self.styles['TableCell']),
                Paragraph(format_list(experience_areas), self.styles['TableCell'])
            ]
        ]
        
        # Create table with equal column widths
        skills_table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        skills_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f497d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(skills_table)
        elements.append(Spacer(1, 0.3 * inch))
        return elements
    
    def _create_detailed_matches_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create detailed matches section as a wide consolidated table"""
        elements = []
        
        heading = Paragraph("Detailed Match Analysis", self.styles['CustomHeading'])
        elements.append(heading)
        
        detailed_matches = analysis_data.get('detailed_matches', [])
        
        if detailed_matches:
            # Limit to top 10 matches to prevent overflow
            matches_to_show = detailed_matches[:10]
            
            # Build table data starting with header
            table_data = [
                [
                    Paragraph('<b>Category</b>', self.styles['TableCell']),
                    Paragraph('<b>Item</b>', self.styles['TableCell']),
                    Paragraph('<b>Profile Evidence</b>', self.styles['TableCell']),
                    Paragraph('<b>JD Requirement</b>', self.styles['TableCell']),
                    Paragraph('<b>Match Strength</b>', self.styles['TableCell'])
                ]
            ]
            
            # Add data rows
            for i, match in enumerate(matches_to_show):
                row = [
                    self._create_table_cell(match.get('category', 'N/A')),
                    self._create_table_cell(match.get('item', 'N/A')),
                    self._create_table_cell(match.get('profile_evidence', 'N/A')),
                    self._create_table_cell(match.get('jd_requirement', 'N/A')),
                    self._create_table_cell(match.get('match_strength', 'N/A'))
                ]
                table_data.append(row)
            
            # Create table with specified column widths
            match_table = Table(table_data, colWidths=[0.9*inch, 0.9*inch, 1.6*inch, 1.6*inch, 0.9*inch])
            
            # Build style rules
            style_rules = [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f497d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
            
            # Add alternating row backgrounds
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    style_rules.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
            
            match_table.setStyle(TableStyle(style_rules))
            
            elements.append(match_table)
            
            # Add note if there are more matches than shown
            if len(detailed_matches) > 10:
                note = Paragraph(
                    f"<i>Note: Showing top 10 of {len(detailed_matches)} matches</i>",
                    self.styles['CustomBody']
                )
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(note)
        else:
            elements.append(Paragraph("No detailed matches available", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.3 * inch))
        return elements
    
    def _create_gaps_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create gaps in profile section as a consolidated table"""
        elements = []
        
        heading = Paragraph("Skills & Qualifications Gaps", self.styles['CustomHeading'])
        elements.append(heading)
        
        gaps = analysis_data.get('gaps_in_profile', [])
        
        if gaps:
            # Build table data starting with header
            table_data = [
                [
                    Paragraph('<b>Requirement</b>', self.styles['TableCell']),
                    Paragraph('<b>Importance</b>', self.styles['TableCell']),
                    Paragraph('<b>Suggestion</b>', self.styles['TableCell']),
                    Paragraph('<b>Timeline</b>', self.styles['TableCell'])
                ]
            ]
            
            # Add data rows
            for gap in gaps:
                importance = gap.get('importance', 'N/A')
                importance_color = {
                    'Critical': colors.red,
                    'Important': colors.orange,
                    'Nice-to-have': colors.blue
                }.get(importance, colors.black)
                
                row = [
                    self._create_table_cell(gap.get('requirement', 'N/A')),
                    Paragraph(f'<font color={importance_color.hexval()}><b>{importance}</b></font>', self.styles['TableCell']),
                    self._create_table_cell(gap.get('suggestion', 'N/A')),
                    self._create_table_cell(gap.get('timeline', 'N/A'))
                ]
                table_data.append(row)
            
            # Create table
            gap_table = Table(table_data, colWidths=[1.8*inch, 1.0*inch, 2.2*inch, 1.0*inch])
            gap_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff3cd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(gap_table)
        else:
            elements.append(Paragraph("No significant gaps identified", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.3 * inch))
        return elements
    
    def _create_strengths_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create profile strengths section as a consolidated table"""
        elements = []
        
        heading = Paragraph("Profile Strengths & Highlights", self.styles['CustomHeading'])
        elements.append(heading)
        
        strengths = analysis_data.get('profile_strengths', [])
        
        if strengths:
            # Build table data starting with header
            table_data = [
                [
                    Paragraph('<b>Skill/Experience</b>', self.styles['TableCell']),
                    Paragraph('<b>Relevance to JD</b>', self.styles['TableCell']),
                    Paragraph('<b>Highlight Strategy</b>', self.styles['TableCell'])
                ]
            ]
            
            # Add data rows
            for strength in strengths:
                row = [
                    self._create_table_cell(strength.get('skill_or_experience', 'N/A')),
                    self._create_table_cell(strength.get('relevance_to_jd', 'N/A')),
                    self._create_table_cell(strength.get('highlight_strategy', 'N/A'))
                ]
                table_data.append(row)
            
            # Create table
            strength_table = Table(table_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
            strength_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d4edda')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(strength_table)
        else:
            elements.append(Paragraph("No specific strengths highlighted", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.3 * inch))
        return elements
    
    def _create_anomalies_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create anomalies section"""
        elements = []
        
        heading = Paragraph("Anomalies & Discrepancies", self.styles['CustomHeading'])
        elements.append(heading)
        
        anomalies = analysis_data.get('anomalies', [])
        
        if anomalies:
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'N/A')
                severity_color = {
                    'High': colors.red,
                    'Medium': colors.orange,
                    'Low': colors.blue
                }.get(severity, colors.black)
                
                anomaly_data = [
                    [self._create_table_cell('Type:'), self._create_table_cell(anomaly.get('type', 'N/A'))],
                    [self._create_table_cell('Severity:'), Paragraph(f'<font color={severity_color.hexval()}><b>{severity}</b></font>', self.styles['TableCell'])],
                    [self._create_table_cell('Description:'), self._create_table_cell(anomaly.get('description', 'N/A'))],
                    [self._create_table_cell('Recommendation:'), self._create_table_cell(anomaly.get('recommendation', 'N/A'))]
                ]
                
                anomaly_table = Table(anomaly_data, colWidths=[1.5*inch, 4.5*inch])
                anomaly_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8d7da')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                elements.append(anomaly_table)
                elements.append(Spacer(1, 0.15 * inch))
        else:
            elements.append(Paragraph("No anomalies detected", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.2 * inch))
        return elements
    
    def _create_hr_recommendation_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create HR recommendation section (without interview questions)"""
        elements = []
        
        # === HR Recommendation ===
        heading = Paragraph("HR Recommendation", self.styles['CustomHeading'])
        elements.append(heading)
        
        hr_recommendation = analysis_data.get('hr_recommendation', {})
        decision = hr_recommendation.get('decision', 'Consider with Reservations')
        reasoning = hr_recommendation.get('reasoning', 'No reasoning provided')
        key_considerations = hr_recommendation.get('key_considerations', [])
        
        # Decision box with color coding
        decision_color = {
            'Proceed to Interview': colors.HexColor('#28a745'),  # Green
            'Consider with Reservations': colors.HexColor('#ffc107'),  # Yellow
            'Do Not Proceed': colors.HexColor('#dc3545')  # Red
        }.get(decision, colors.HexColor('#6c757d'))  # Default gray
        
        decision_data = [[
            Paragraph(f"<font size=18 color={decision_color.hexval()}><b>{decision}</b></font>",
                     self.styles['CustomBody'])
        ]]
        
        decision_table = Table(decision_data, colWidths=[6*inch])
        decision_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, decision_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        elements.append(decision_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Reasoning
        subheading = Paragraph("Reasoning", self.styles['CustomSubHeading'])
        elements.append(subheading)
        reasoning_para = Paragraph(reasoning, self.styles['CustomBody'])
        elements.append(reasoning_para)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Key Considerations
        if key_considerations:
            subheading = Paragraph("Key Considerations for HR", self.styles['CustomSubHeading'])
            elements.append(subheading)
            
            for consideration in key_considerations:
                bullet = Paragraph(f"• {consideration}", self.styles['CustomBody'])
                elements.append(bullet)
            
            elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_interview_questions_section(self, analysis_data: Dict[str, Any]) -> list:
        """Create interview questions section with bulleted format"""
        elements = []
        
        heading = Paragraph("Interview Preparation", self.styles['CustomHeading'])
        elements.append(heading)
        
        interview_questions = analysis_data.get('interview_questions', {})
        technical_questions = interview_questions.get('technical_questions', [])
        behavioral_questions = interview_questions.get('behavioral_questions', [])
        
        # Technical Questions
        if technical_questions:
            subheading = Paragraph("Technical Questions", self.styles['CustomSubHeading'])
            elements.append(subheading)
            
            for question in technical_questions:
                bullet = Paragraph(f"• {question}", self.styles['CustomBody'])
                elements.append(bullet)
            
            elements.append(Spacer(1, 0.2 * inch))
        
        # Behavioral Questions
        if behavioral_questions:
            subheading = Paragraph("Behavioral Questions", self.styles['CustomSubHeading'])
            elements.append(subheading)
            
            for question in behavioral_questions:
                bullet = Paragraph(f"• {question}", self.styles['CustomBody'])
                elements.append(bullet)
            
            elements.append(Spacer(1, 0.2 * inch))
        
        if not technical_questions and not behavioral_questions:
            elements.append(Paragraph("No interview questions available", self.styles['CustomBody']))
            elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def generate_report(
        self,
        analysis_data: Dict[str, Any],
        output_filename: str = None
    ) -> Optional[bytes]:
        """
        Generate PDF report from analysis data
        
        Args:
            analysis_data: Dictionary containing analysis results
            output_filename: Optional filename for saving (if None, returns bytes)
            
        Returns:
            PDF as bytes if output_filename is None, else None
        """
        try:
            # Create PDF document
            if output_filename:
                doc = SimpleDocTemplate(
                    output_filename,
                    pagesize=self.page_size,
                    topMargin=0.75*inch,
                    bottomMargin=0.75*inch,
                    leftMargin=0.75*inch,
                    rightMargin=0.75*inch
                )
                buffer = None
            else:
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=self.page_size,
                    topMargin=0.75*inch,
                    bottomMargin=0.75*inch,
                    leftMargin=0.75*inch,
                    rightMargin=0.75*inch
                )
            
            # Build report elements
            elements = []
            
            # Add sections
            elements.extend(self._create_header(analysis_data))
            elements.extend(self._create_overall_match_section(analysis_data))
            elements.extend(self._create_matching_skills_section(analysis_data))
            elements.extend(self._create_hr_recommendation_section(analysis_data))
            elements.append(PageBreak())
            elements.extend(self._create_detailed_matches_section(analysis_data))
            elements.append(PageBreak())
            elements.extend(self._create_gaps_section(analysis_data))
            elements.extend(self._create_strengths_section(analysis_data))
            elements.append(PageBreak())
            elements.extend(self._create_anomalies_section(analysis_data))
            elements.append(PageBreak())
            elements.extend(self._create_interview_questions_section(analysis_data))
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Report generated successfully")
            
            if buffer:
                return buffer.getvalue()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return None


def generate_pdf_report(analysis_data: Dict[str, Any], output_filename: str = None) -> Optional[bytes]:
    """
    Convenience function to generate PDF report
    
    Args:
        analysis_data: Analysis results dictionary
        output_filename: Optional output filename
        
    Returns:
        PDF bytes if no filename provided, else None
    """
    generator = ReportGenerator()
    return generator.generate_report(analysis_data, output_filename)
