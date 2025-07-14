import streamlit as st
from typing import List, Dict, Any, Tuple
import json
import pandas as pd
from datetime import datetime
from src.output import JSONHandler, MarkdownHandler, ExcelHandler
from src.utils.image_utils import ImageUtils

def display_results(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Display processing results with download options"""
    
    st.header("📊 Results")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(results)
    successful = sum(1 for r in results if 'error' not in r)
    failed = total - successful
    
    with col1:
        st.metric("Total Images", total)
    
    with col2:
        st.metric("Successful", successful, delta=f"{(successful/total*100):.0f}%")
    
    with col3:
        st.metric("Failed", failed)
    
    with col4:
        # Average confidence for OCR results
        confidences = []
        for r in results:
            if 'confidence' in r:
                confidences.append(r['confidence'])
            elif 'ocr_result' in r and r['ocr_result'] and 'confidence' in r['ocr_result']:
                confidences.append(r['ocr_result']['confidence'])
        
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            st.metric("Avg Confidence", f"{avg_conf:.1f}%")
    
    st.divider()
    
    # Display options
    display_mode = st.radio(
        "Display Mode",
        ["Summary", "Detailed", "Raw JSON"],
        horizontal=True
    )
    
    # Results display
    if display_mode == "Summary":
        _display_summary(results, config)
    elif display_mode == "Detailed":
        _display_detailed(results, config)
    else:  # Raw JSON
        _display_raw_json(results)
    
    # Download section
    st.divider()
    st.subheader("💾 Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    output_format = config.get('output_format', 'JSON')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with col1:
        # Primary format download
        if st.button(f"Download as {output_format}", type="primary"):
            file_path, file_data = _generate_output_file(results, output_format, timestamp)
            
            st.download_button(
                label=f"📥 Download {output_format}",
                data=file_data,
                file_name=file_path,
                mime="application/octet-stream"
            )
    
    with col2:
        # Alternative format download
        alt_format = "JSON" if output_format != "JSON" else "Markdown"
        if st.button(f"Download as {alt_format}"):
            file_path, file_data = _generate_output_file(results, alt_format, timestamp)
            
            st.download_button(
                label=f"📥 Download {alt_format}",
                data=file_data,
                file_name=file_path,
                mime="application/octet-stream"
            )
    
    with col3:
        # Download preprocessing report if available
        if any('processing_info' in r for r in results):
            if st.button("Download Processing Report"):
                report = _generate_processing_report(results)
                
                st.download_button(
                    label="📥 Download Report",
                    data=report,
                    file_name=f"processing_report_{timestamp}.md",
                    mime="text/markdown"
                )

def _display_summary(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Display results in summary format"""
    
    # Group results by status
    successful_results = [r for r in results if 'error' not in r]
    failed_results = [r for r in results if 'error' in r]
    
    if successful_results:
        st.subheader("✅ Successful Extractions")
        
        # Create summary table
        summary_data = []
        
        for result in successful_results:
            row = {
                'File': result.get('filename', 'Unknown'),
                'Mode': result.get('mode', config.get('mode', 'Unknown'))
            }
            
            # Add key extracted data
            if 'text' in result:
                row['Extracted'] = f"{len(result['text'].split())} words"
            elif 'data' in result and isinstance(result['data'], dict):
                row['Extracted'] = f"{len(result['data'])} fields"
            elif 'llm_result' in result:
                row['Extracted'] = "Structured data"
            else:
                row['Extracted'] = "Data extracted"
            
            # Add confidence if available
            if 'confidence' in result:
                row['Confidence'] = f"{result['confidence']:.1f}%"
            elif 'ocr_result' in result and result['ocr_result'] and 'confidence' in result['ocr_result']:
                row['Confidence'] = f"{result['ocr_result']['confidence']:.1f}%"
            
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True)
    
    if failed_results:
        st.subheader("❌ Failed Extractions")
        
        for result in failed_results:
            with st.expander(f"🔴 {result.get('filename', 'Unknown')}"):
                st.error(result.get('error', 'Unknown error'))

def _display_detailed(results: List[Dict[str, Any]], config: Dict[str, Any]):
    """Display detailed results for each image"""
    
    for idx, result in enumerate(results):
        filename = result.get('filename', f'Image {idx + 1}')
        
        # Create expander for each result
        with st.expander(f"📄 {filename}", expanded=(idx == 0)):
            
            if 'error' in result:
                st.error(f"Processing failed: {result['error']}")
            else:
                # Display based on processing mode
                mode = result.get('mode', config.get('mode'))
                
                if mode == "Standard OCR" or 'text' in result:
                    _display_ocr_result(result)
                
                elif mode == "LLM-based" or 'data' in result:
                    _display_llm_result(result)
                
                elif mode == "OCR + LLM Extraction" or ('ocr_result' in result and 'llm_result' in result):
                    _display_hybrid_result(result)
                
                # Show preprocessing info if available
                if 'processing_info' in result:
                    _display_preprocessing_info(result['processing_info'])

def _display_ocr_result(result: Dict[str, Any]):
    """Display OCR-specific results"""
    st.subheader("📝 Extracted Text")
    
    text = result.get('text', '')
    if text:
        st.text_area("", text, height=200, disabled=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", len(text.split()))
        with col2:
            st.metric("Characters", len(text))
        with col3:
            if 'confidence' in result:
                st.metric("Confidence", f"{result['confidence']:.1f}%")
    else:
        st.warning("No text extracted")

def _display_llm_result(result: Dict[str, Any]):
    """Display LLM extraction results"""
    st.subheader("🤖 Extracted Data")
    
    data = result.get('data', {})
    
    if isinstance(data, dict):
        # Display as formatted JSON
        st.json(data)
        
        # Also show in table format if possible
        if len(data) > 0 and all(isinstance(v, (str, int, float, bool)) for v in data.values()):
            st.subheader("📊 Table View")
            df = pd.DataFrame([data])
            st.dataframe(df)
    else:
        st.text(str(data))

def _display_hybrid_result(result: Dict[str, Any]):
    """Display hybrid mode results"""
    
    # OCR Results
    if 'ocr_result' in result and result['ocr_result']:
        st.subheader("📝 OCR Extraction")
        ocr_data = result['ocr_result']
        
        col1, col2 = st.columns([3, 1])
        with col1:
            text = ocr_data.get('text', '')
            if text:
                st.text_area("", text, height=150, disabled=True)
        with col2:
            if 'confidence' in ocr_data:
                st.metric("OCR Confidence", f"{ocr_data['confidence']:.1f}%")
            if 'word_count' in ocr_data:
                st.metric("Words", ocr_data['word_count'])
    
    # LLM Results
    if 'llm_result' in result and result['llm_result']:
        st.subheader("🤖 LLM Extraction")
        llm_data = result['llm_result']
        
        if isinstance(llm_data, dict):
            st.json(llm_data)
        else:
            st.text(str(llm_data))

def _display_preprocessing_info(info: Dict[str, Any]):
    """Display preprocessing information"""
    
    with st.expander("🔧 Preprocessing Details"):
        if 'applied_steps' in info and info['applied_steps']:
            st.write("**Applied Steps:**")
            for step in info['applied_steps']:
                st.write(f"• {step}")
        
        if 'quality_improvement' in info:
            improvement = info['quality_improvement']
            if improvement > 0:
                st.success(f"Quality improved by {improvement:.1f}%")
            elif improvement < 0:
                st.warning(f"Quality decreased by {abs(improvement):.1f}%")
        
        # Show metrics comparison if available
        if 'original_metrics' in info and 'processed_metrics' in info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Metrics:**")
                for key, value in info['original_metrics'].items():
                    if isinstance(value, (int, float)):
                        st.write(f"• {key}: {value:.2f}")
            
            with col2:
                st.write("**Processed Metrics:**")
                for key, value in info['processed_metrics'].items():
                    if isinstance(value, (int, float)):
                        st.write(f"• {key}: {value:.2f}")

def _display_raw_json(results: List[Dict[str, Any]]):
    """Display raw JSON results"""
    st.json(results)

def _generate_output_file(results: List[Dict[str, Any]], format: str, timestamp: str) -> Tuple[str, bytes]:
    """Generate output file in specified format"""
    
    if format == "JSON":
        handler = JSONHandler()
        filename = f"ocr_results_{timestamp}.json"
        content = handler.to_string(results)
        return filename, content.encode('utf-8')
    
    elif format == "Markdown":
        handler = MarkdownHandler()
        filename = f"ocr_results_{timestamp}.md"
        content = handler.to_string(results)
        return filename, content.encode('utf-8')
    
    elif format == "XLSX":
        handler = ExcelHandler()
        filename = f"ocr_results_{timestamp}.xlsx"
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            handler.save(results, tmp.name)
            with open(tmp.name, 'rb') as f:
                content = f.read()
            
            # Clean up
            import os
            os.unlink(tmp.name)
            
            return filename, content
    
    else:
        # Default to JSON
        return _generate_output_file(results, "JSON", timestamp)

def _generate_processing_report(results: List[Dict[str, Any]]) -> str:
    """Generate detailed processing report"""
    
    report = ["# OCR Processing Report\n"]
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"Total Images: {len(results)}\n\n")
    
    # Summary statistics
    report.append("## Summary\n")
    successful = sum(1 for r in results if 'error' not in r)
    report.append(f"- Successful: {successful}/{len(results)}\n")
    report.append(f"- Failed: {len(results) - successful}/{len(results)}\n\n")
    
    # Preprocessing statistics
    preprocessing_count = sum(1 for r in results if 'processing_info' in r)
    if preprocessing_count > 0:
        report.append("## Preprocessing Statistics\n")
        report.append(f"- Images preprocessed: {preprocessing_count}\n")
        
        # Collect all applied steps
        all_steps = []
        for r in results:
            if 'processing_info' in r and 'applied_steps' in r['processing_info']:
                all_steps.extend(r['processing_info']['applied_steps'])
        
        if all_steps:
            from collections import Counter
            step_counts = Counter(all_steps)
            report.append("\n### Most Common Preprocessing Steps:\n")
            for step, count in step_counts.most_common():
                report.append(f"- {step}: {count} times\n")
    
    report.append("\n## Detailed Results\n")
    
    # Individual results
    for idx, result in enumerate(results):
        report.append(f"\n### {idx + 1}. {result.get('filename', 'Unknown')}\n")
        
        if 'error' in result:
            report.append(f"**Status:** Failed\n")
            report.append(f"**Error:** {result['error']}\n")
        else:
            report.append(f"**Status:** Success\n")
            report.append(f"**Mode:** {result.get('mode', 'Unknown')}\n")
            
            if 'processing_info' in result:
                info = result['processing_info']
                if 'applied_steps' in info:
                    report.append(f"**Preprocessing:** {', '.join(info['applied_steps'])}\n")
                if 'quality_improvement' in info:
                    report.append(f"**Quality Change:** {info['quality_improvement']:+.1f}%\n")
    
    return '\n'.join(report)