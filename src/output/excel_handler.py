import pandas as pd
from typing import List, Dict, Any
from .base_handler import BaseOutputHandler
import json

class ExcelHandler(BaseOutputHandler):
    """Handler for Excel output format"""
    
    def save(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """Save results as Excel file"""
        self.ensure_directory(output_path)
        
        # Convert results to DataFrame-friendly format
        df_data = self._prepare_dataframe_data(results)
        
        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Save to Excel with formatting
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Extraction Results', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Extraction Results']
            for column in df:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
        
        return output_path
    
    def format_single_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single result for Excel"""
        row = {
            'filename': result.get('filename', 'unknown'),
            'status': 'error' if 'error' in result else 'success',
            'processing_mode': result.get('mode', 'unknown')
        }
        
        if 'error' in result:
            row['error'] = result['error']
        else:
            # Handle different data structures
            if 'text' in result:
                # Simple OCR result
                row['extracted_text'] = result['text']
                row['confidence'] = result.get('confidence', '')
                row['word_count'] = result.get('word_count', '')
            
            elif 'data' in result:
                # LLM structured data
                data = result['data']
                if isinstance(data, dict):
                    # Flatten nested dictionary
                    for key, value in data.items():
                        if isinstance(value, (str, int, float, bool)):
                            row[f'data_{key}'] = value
                        else:
                            row[f'data_{key}'] = json.dumps(value, ensure_ascii=False)
                else:
                    row['extracted_data'] = str(data)
            
            elif 'ocr_result' in result:
                # Hybrid mode
                ocr_data = result['ocr_result']
                row['ocr_text'] = ocr_data.get('text', '')
                row['ocr_confidence'] = ocr_data.get('confidence', '')
                
                if result.get('llm_result'):
                    llm_data = result['llm_result']
                    if isinstance(llm_data, dict):
                        for key, value in llm_data.items():
                            if isinstance(value, (str, int, float, bool)):
                                row[f'llm_{key}'] = value
                            else:
                                row[f'llm_{key}'] = json.dumps(value, ensure_ascii=False)
                    else:
                        row['llm_extraction'] = str(llm_data)
        
        # Add processing info if available
        if 'processing_info' in result:
            info = result['processing_info']
            if info.get('applied_steps'):
                row['preprocessing_steps'] = ', '.join(info['applied_steps'])
            if info.get('quality_improvement') is not None:
                row['quality_improvement'] = f"{info['quality_improvement']:.1f}%"
        
        return row
    
    def _prepare_dataframe_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for DataFrame creation"""
        df_data = []
        
        for result in results:
            row = self.format_single_result(result)
            df_data.append(row)
        
        return df_data
    
    def save_multi_sheet(self, results: List[Dict[str, Any]], output_path: str, 
                        include_details: bool = True) -> str:
        """Save results to Excel with multiple sheets for better organization"""
        self.ensure_directory(output_path)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main results sheet
            main_df = pd.DataFrame(self._prepare_dataframe_data(results))
            main_df.to_excel(writer, sheet_name='Summary', index=False)
            
            if include_details:
                # Separate sheets for different processing modes
                mode_groups = {}
                for i, result in enumerate(results):
                    mode = result.get('mode', 'unknown')
                    if mode not in mode_groups:
                        mode_groups[mode] = []
                    mode_groups[mode].append((i, result))
                
                for mode, mode_results in mode_groups.items():
                    if mode_results:
                        mode_df_data = []
                        for idx, result in mode_results:
                            detailed_row = self._create_detailed_row(idx, result)
                            mode_df_data.append(detailed_row)
                        
                        mode_df = pd.DataFrame(mode_df_data)
                        sheet_name = f"{mode[:30]}"  # Excel sheet name limit
                        mode_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Statistics sheet
            stats_df = self._create_statistics_dataframe(results)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        return output_path
    
    def _create_detailed_row(self, index: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed row with all available information"""
        row = {
            'index': index + 1,
            'filename': result.get('filename', 'unknown')
        }
        
        # Flatten all nested data
        def flatten_dict(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                elif isinstance(v, list):
                    items.append((new_key, json.dumps(v, ensure_ascii=False)))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        # Remove filename to avoid duplication
        result_copy = result.copy()
        result_copy.pop('filename', None)
        
        flattened = flatten_dict(result_copy)
        row.update(flattened)
        
        return row
    
    def _create_statistics_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create statistics summary DataFrame"""
        stats = {
            'Metric': [],
            'Value': []
        }
        
        # Basic counts
        stats['Metric'].append('Total Images')
        stats['Value'].append(len(results))
        
        stats['Metric'].append('Successful')
        stats['Value'].append(sum(1 for r in results if 'error' not in r))
        
        stats['Metric'].append('Failed')
        stats['Value'].append(sum(1 for r in results if 'error' in r))
        
        # Mode breakdown
        mode_counts = {}
        for result in results:
            mode = result.get('mode', 'unknown')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        for mode, count in mode_counts.items():
            stats['Metric'].append(f'Mode: {mode}')
            stats['Value'].append(count)
        
        # Average confidence for OCR results
        ocr_confidences = []
        for result in results:
            if 'confidence' in result:
                ocr_confidences.append(result['confidence'])
            elif 'ocr_result' in result and 'confidence' in result['ocr_result']:
                ocr_confidences.append(result['ocr_result']['confidence'])
        
        if ocr_confidences:
            stats['Metric'].append('Average OCR Confidence')
            stats['Value'].append(f"{sum(ocr_confidences) / len(ocr_confidences):.1f}%")
        
        return pd.DataFrame(stats)