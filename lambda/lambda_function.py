import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def clean_and_normalize_text(text):
    """Advanced text cleaning and normalization"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>]', ' ', text)
    
    # Fix multiple punctuation
    text = re.sub(r'([.!?]){2,}', r'\1', text)
    text = re.sub(r'([,;:]){2,}', r'\1', text)
    
    # Normalize quotes
    text = re.sub(r'[""]', '"', text)
    text = re.sub(r'['']', "'", text)
    
    # Remove excessive spaces around punctuation
    text = re.sub(r'\s+([.!?,:;])', r'\1', text)
    text = re.sub(r'([.!?])\s+', r'\1 ', text)
    
    # Strip and return
    return text.strip()

def extract_text_with_tags(soup):
    """Extract text content with HTML tag information preserved"""
    text_elements = []
    
    # Process different types of content elements
    content_tags = [
        'p', 'div', 'span', 'article', 'section', 'main', 'header', 'footer',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'dl', 'dt', 'dd',
        'blockquote', 'q', 'cite',
        'strong', 'b', 'em', 'i', 'mark', 'small',
        'pre', 'code', 'kbd', 'samp', 'var',
        'a', 'abbr', 'acronym', 'address',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'figcaption', 'caption', 'summary', 'details'
    ]
    
    for tag_name in content_tags:
        elements = soup.find_all(tag_name)
        for i, element in enumerate(elements):
            try:
                # Skip if element is empty or only whitespace
                text_content = element.get_text(strip=True)
                if not text_content:
                    continue
                
                # Clean the text
                cleaned_text = clean_and_normalize_text(text_content)
                if not cleaned_text or len(cleaned_text) < 3:
                    continue
                
                # Get element attributes
                element_id = element.get('id', '')
                element_class = ' '.join(element.get('class', []))
                
                # Determine content type and importance
                importance_score = get_content_importance(tag_name, element_class, element_id)
                content_type = classify_content_type(tag_name, cleaned_text, element_class)
                
                # Extract additional metadata
                parent_tag = element.parent.name if element.parent else ''
                word_count = len(cleaned_text.split())
                char_count = len(cleaned_text)
                
                text_element = {
                    'tag': tag_name,
                    'text': cleaned_text,
                    'text_preview': cleaned_text[:100] + ('...' if len(cleaned_text) > 100 else ''),
                    'position': i + 1,
                    'word_count': word_count,
                    'char_count': char_count,
                    'element_id': element_id,
                    'element_class': element_class,
                    'parent_tag': parent_tag,
                    'importance_score': importance_score,
                    'content_type': content_type,
                    'has_links': bool(element.find('a')),
                    'has_images': bool(element.find('img')),
                    'has_formatting': bool(element.find(['strong', 'b', 'em', 'i', 'mark'])),
                    'is_heading': tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                    'is_navigation': 'nav' in element_class.lower() or element_id.lower() == 'nav',
                    'is_main_content': content_type in ['main_content', 'article'],
                    'sentence_count': len(re.findall(r'[.!?]+', cleaned_text))
                }
                
                text_elements.append(text_element)
                
            except Exception as e:
                logger.warning(f"Error processing {tag_name} element: {str(e)}")
                continue
    
    return text_elements

def get_content_importance(tag_name, element_class, element_id):
    """Calculate importance score for content elements (1-10)"""
    score = 5  # Base score
    
    # Tag-based scoring
    tag_scores = {
        'h1': 10, 'h2': 9, 'h3': 8, 'h4': 7, 'h5': 6, 'h6': 6,
        'title': 10, 'p': 6, 'article': 9, 'main': 9,
        'section': 7, 'div': 5, 'span': 4,
        'blockquote': 7, 'strong': 6, 'em': 6,
        'figcaption': 6, 'caption': 6, 'summary': 7
    }
    score = tag_scores.get(tag_name, score)
    
    # Class-based adjustments
    if element_class:
        class_lower = element_class.lower()
        if any(keyword in class_lower for keyword in ['main', 'content', 'article', 'post']):
            score += 2
        elif any(keyword in class_lower for keyword in ['sidebar', 'footer', 'nav', 'menu']):
            score -= 2
        elif any(keyword in class_lower for keyword in ['title', 'heading', 'header']):
            score += 1
    
    # ID-based adjustments
    if element_id:
        id_lower = element_id.lower()
        if any(keyword in id_lower for keyword in ['main', 'content', 'article']):
            score += 2
        elif any(keyword in id_lower for keyword in ['sidebar', 'footer', 'nav']):
            score -= 2
    
    return max(1, min(10, score))

def classify_content_type(tag_name, text_content, element_class):
    """Classify the type of content"""
    class_lower = element_class.lower() if element_class else ''
    text_lower = text_content.lower()
    
    # Heading content
    if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return 'heading'
    
    # Navigation content
    if any(keyword in class_lower for keyword in ['nav', 'menu', 'breadcrumb']):
        return 'navigation'
    
    # Main content indicators
    if any(keyword in class_lower for keyword in ['main', 'content', 'article', 'post', 'entry']):
        return 'main_content'
    
    # Sidebar content
    if any(keyword in class_lower for keyword in ['sidebar', 'aside', 'widget']):
        return 'sidebar'
    
    # Footer content
    if any(keyword in class_lower for keyword in ['footer', 'copyright']):
        return 'footer'
    
    # Header content
    if any(keyword in class_lower for keyword in ['header', 'banner', 'logo']):
        return 'header'
    
    # Form content
    if tag_name in ['form', 'input', 'button', 'select', 'textarea']:
        return 'form'
    
    # List content
    if tag_name in ['ul', 'ol', 'li', 'dl', 'dt', 'dd']:
        return 'list'
    
    # Quote content
    if tag_name in ['blockquote', 'q', 'cite']:
        return 'quote'
    
    # Code content
    if tag_name in ['pre', 'code', 'kbd', 'samp', 'var']:
        return 'code'
    
    # Table content
    if tag_name in ['table', 'thead', 'tbody', 'tr', 'th', 'td']:
        return 'table'
    
    # Link content
    if tag_name == 'a':
        return 'link'
    
    # Paragraph content (default for most text)
    if tag_name in ['p', 'div', 'span']:
        # Check if it looks like main content based on length
        if len(text_content) > 100:
            return 'paragraph'
        else:
            return 'short_text'
    
    return 'general'

def extract_enhanced_headings(soup):
    """Extract headings with comprehensive metadata and hierarchy analysis"""
    headings = []
    heading_hierarchy = {'h1': 0, 'h2': 0, 'h3': 0, 'h4': 0, 'h5': 0, 'h6': 0}
    
    for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level_headings = soup.find_all(level)
        heading_hierarchy[level] = len(level_headings)
        
        for idx, heading in enumerate(level_headings):
            try:
                text_content = heading.get_text(strip=True)
                if not text_content:
                    continue
                
                cleaned_text = clean_and_normalize_text(text_content)
                if not cleaned_text:
                    continue
                
                # Extract styling and structure info
                element_id = heading.get('id', '')
                element_class = ' '.join(heading.get('class', []))
                parent_element = heading.parent.name if heading.parent else ''
                
                # Analyze heading content
                word_count = len(cleaned_text.split())
                has_numbers = bool(re.search(r'\d+', cleaned_text))
                has_special_chars = bool(re.search(r'[^\w\s]', cleaned_text))
                is_question = cleaned_text.strip().endswith('?')
                
                # Check for nested elements
                has_links = bool(heading.find('a'))
                has_emphasis = bool(heading.find(['strong', 'b', 'em', 'i']))
                has_images = bool(heading.find('img'))
                
                # Determine heading type
                heading_type = classify_heading_type(cleaned_text, level, element_class)
                
                # Calculate hierarchy position
                level_num = int(level[1])
                hierarchy_position = f"{level_num}.{idx + 1}"
                
                heading_data = {
                    'level': level,
                    'level_number': level_num,
                    'position_in_level': idx + 1,
                    'hierarchy_position': hierarchy_position,
                    'text': cleaned_text,
                    'text_length': len(cleaned_text),
                    'word_count': word_count,
                    'element_id': element_id,
                    'element_class': element_class,
                    'parent_element': parent_element,
                    'heading_type': heading_type,
                    'has_id': bool(element_id),
                    'has_class': bool(element_class),
                    'has_links': has_links,
                    'has_emphasis': has_emphasis,
                    'has_images': has_images,
                    'has_numbers': has_numbers,
                    'has_special_chars': has_special_chars,
                    'is_question': is_question,
                    'is_seo_friendly': 10 <= word_count <= 60,
                    'accessibility_score': calculate_heading_accessibility(heading, cleaned_text)
                }
                
                headings.append(heading_data)
                
            except Exception as e:
                logger.warning(f"Error processing {level} heading: {str(e)}")
                continue
    
    return headings, heading_hierarchy

def classify_heading_type(text, level, element_class):
    """Classify the type/purpose of a heading"""
    text_lower = text.lower()
    class_lower = element_class.lower() if element_class else ''
    
    # Navigation headings
    if any(keyword in class_lower for keyword in ['nav', 'menu']):
        return 'navigation'
    
    # Section headings based on common patterns
    if any(keyword in text_lower for keyword in ['about', 'introduction', 'overview']):
        return 'introduction'
    elif any(keyword in text_lower for keyword in ['contact', 'get in touch', 'reach out']):
        return 'contact'
    elif any(keyword in text_lower for keyword in ['service', 'what we do', 'offering']):
        return 'services'
    elif any(keyword in text_lower for keyword in ['product', 'features', 'specification']):
        return 'product'
    elif any(keyword in text_lower for keyword in ['news', 'blog', 'article', 'post']):
        return 'content'
    elif any(keyword in text_lower for keyword in ['team', 'staff', 'people', 'member']):
        return 'team'
    elif any(keyword in text_lower for keyword in ['testimonial', 'review', 'feedback']):
        return 'testimonial'
    elif any(keyword in text_lower for keyword in ['faq', 'question', 'help', 'support']):
        return 'faq'
    elif any(keyword in text_lower for keyword in ['price', 'cost', 'plan', 'package']):
        return 'pricing'
    elif text_lower.endswith('?'):
        return 'question'
    elif level == 'h1':
        return 'main_title'
    elif level in ['h2', 'h3']:
        return 'section_title'
    else:
        return 'subsection'

def calculate_heading_accessibility(heading_element, text):
    """Calculate accessibility score for headings"""
    score = 5  # Base score
    
    # Length check
    if 10 <= len(text) <= 60:
        score += 2
    elif len(text) > 100:
        score -= 2
    
    # ID presence for anchor links
    if heading_element.get('id'):
        score += 1
    
    # Avoid all caps
    if text.isupper():
        score -= 1
    
    # Check for descriptive content
    if len(text.split()) >= 3:
        score += 1
    
    return max(1, min(10, score))

def extract_comprehensive_content_blocks(soup):
    """Extract and analyze content blocks with detailed metadata"""
    content_blocks = []
    
    # Define content containers
    content_containers = soup.find_all([
        'article', 'section', 'main', 'div', 'aside',
        'header', 'footer', 'nav', 'p', 'blockquote'
    ])
    
    for idx, container in enumerate(content_containers):
        try:
            # Skip if container is empty or too small
            text_content = container.get_text(strip=True)
            if not text_content or len(text_content) < 10:
                continue
            
            cleaned_text = clean_and_normalize_text(text_content)
            if not cleaned_text:
                continue
            
            # Get container metadata
            tag_name = container.name
            element_id = container.get('id', '')
            element_class = ' '.join(container.get('class', []))
            
            # Analyze content structure
            child_tags = [child.name for child in container.find_all() if child.name]
            unique_child_tags = list(set(child_tags))
            
            # Count specific elements
            paragraph_count = len(container.find_all('p'))
            heading_count = len(container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            link_count = len(container.find_all('a'))
            image_count = len(container.find_all('img'))
            list_count = len(container.find_all(['ul', 'ol']))
            
            # Text analysis
            word_count = len(cleaned_text.split())
            sentence_count = len(re.findall(r'[.!?]+', cleaned_text))
            paragraph_text_count = len([p for p in cleaned_text.split('\n') if p.strip()])
            
            # Content classification
            content_type = classify_content_block(tag_name, element_class, element_id, cleaned_text)
            importance_score = calculate_content_importance(
                tag_name, element_class, word_count, heading_count, link_count
            )
            
            # Language and readability analysis
            avg_word_length = sum(len(word) for word in cleaned_text.split()) / max(word_count, 1)
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            content_block = {
                'block_id': idx + 1,
                'tag': tag_name,
                'text': cleaned_text,
                'text_preview': cleaned_text[:200] + ('...' if len(cleaned_text) > 200 else ''),
                'word_count': word_count,
                'char_count': len(cleaned_text),
                'sentence_count': sentence_count,
                'paragraph_count': paragraph_text_count,
                'element_id': element_id,
                'element_class': element_class,
                'content_type': content_type,
                'importance_score': importance_score,
                'child_elements': len(child_tags),
                'unique_child_types': len(unique_child_tags),
                'child_tags': ', '.join(unique_child_tags[:10]),  # Limit for readability
                'heading_count': heading_count,
                'paragraph_count': paragraph_count,
                'link_count': link_count,
                'image_count': image_count,
                'list_count': list_count,
                'has_structured_content': heading_count > 0 or list_count > 0,
                'is_interactive': link_count > 0 or bool(container.find(['button', 'input', 'form'])),
                'reading_time_minutes': word_count // 250,
                'avg_word_length': round(avg_word_length, 2),
                'avg_sentence_length': round(avg_sentence_length, 2),
                'readability_score': calculate_readability_score(
                    avg_sentence_length, avg_word_length, word_count
                )
            }
            
            content_blocks.append(content_block)
            
        except Exception as e:
            logger.warning(f"Error processing content block: {str(e)}")
            continue
    
    return content_blocks

def classify_content_block(tag_name, element_class, element_id, text_content):
    """Classify content blocks by purpose and type"""
    class_lower = element_class.lower() if element_class else ''
    id_lower = element_id.lower() if element_id else ''
    text_sample = text_content[:200].lower()
    
    # Main content identification
    if tag_name == 'main' or 'main' in class_lower or 'main' in id_lower:
        return 'main_content'
    
    # Article content
    if tag_name == 'article' or 'article' in class_lower:
        return 'article'
    
    # Navigation
    if tag_name == 'nav' or any(nav_term in class_lower for nav_term in ['nav', 'menu', 'breadcrumb']):
        return 'navigation'
    
    # Header/Banner
    if tag_name == 'header' or any(header_term in class_lower for header_term in ['header', 'banner', 'hero']):
        return 'header'
    
    # Footer
    if tag_name == 'footer' or 'footer' in class_lower:
        return 'footer'
    
    # Sidebar
    if tag_name == 'aside' or any(aside_term in class_lower for aside_term in ['sidebar', 'aside', 'widget']):
        return 'sidebar'
    
    # Forms
    if any(form_term in class_lower for form_term in ['form', 'contact', 'subscribe', 'newsletter']):
        return 'form'
    
    # Content sections based on text analysis
    if any(about_term in text_sample for about_term in ['about us', 'our story', 'who we are']):
        return 'about'
    elif any(service_term in text_sample for service_term in ['our services', 'what we do', 'services']):
        return 'services'
    elif any(contact_term in text_sample for contact_term in ['contact us', 'get in touch', 'reach out']):
        return 'contact'
    elif any(product_term in text_sample for product_term in ['our products', 'products', 'catalog']):
        return 'products'
    
    # Default classification based on tag
    tag_classifications = {
        'section': 'section',
        'div': 'content_block',
        'p': 'paragraph',
        'blockquote': 'quote',
        'figure': 'media',
        'table': 'data_table'
    }
    
    return tag_classifications.get(tag_name, 'general_content')

def calculate_content_importance(tag_name, element_class, word_count, heading_count, link_count):
    """Calculate importance score for content blocks"""
    score = 5  # Base score
    
    # Tag-based scoring
    tag_scores = {
        'main': 10, 'article': 9, 'section': 7, 'header': 6,
        'div': 5, 'p': 6, 'aside': 4, 'footer': 3, 'nav': 4
    }
    score = tag_scores.get(tag_name, score)
    
    # Class-based adjustments
    if element_class:
        class_lower = element_class.lower()
        if any(keyword in class_lower for keyword in ['main', 'content', 'primary']):
            score += 3
        elif any(keyword in class_lower for keyword in ['sidebar', 'secondary', 'widget']):
            score -= 2
        elif any(keyword in class_lower for keyword in ['footer', 'copyright']):
            score -= 3
    
    # Content length scoring
    if word_count > 100:
        score += 2
    elif word_count > 50:
        score += 1
    elif word_count < 10:
        score -= 2
    
    # Structure scoring
    if heading_count > 0:
        score += 1
    if link_count > 0:
        score += 0.5
    
    return max(1, min(10, int(score)))

def calculate_readability_score(avg_sentence_length, avg_word_length, word_count):
    """Calculate readability score (simplified Flesch-like formula)"""
    if word_count < 10:
        return 0
    
    # Simplified readability calculation
    base_score = 206.835
    sentence_factor = 1.015 * avg_sentence_length
    word_factor = 84.6 * avg_word_length
    
    score = base_score - sentence_factor - word_factor
    
    # Normalize to 1-10 scale
    normalized_score = max(1, min(10, int((score / 100) * 10)))
    
    return normalized_score

def extract_structured_data(soup, url):
    """Extract structured data including JSON-LD, microdata, and other structured formats"""
    structured_data = {
        'json_ld': [],
        'microdata': [],
        'meta_tags': [],
        'social_media': {},
        'contact_info': {},
        'forms': [],
        'media': []
    }
    
    # Extract JSON-LD structured data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            structured_data['json_ld'].append(data)
        except:
            pass
    
    # Extract microdata
    try:
        microdata_items = soup.find_all(attrs={'itemscope': True})
        for item in microdata_items:
            try:
                item_data = {
                    'itemtype': item.get('itemtype'),
                    'properties': {}
                }
                props = item.find_all(attrs={'itemprop': True})
                for prop in props:
                    try:
                        prop_name = prop.get('itemprop')
                        if prop_name:
                            prop_value = prop.get_text().strip() or prop.get('content', prop.get('src', ''))
                            item_data['properties'][prop_name] = prop_value
                    except Exception as e:
                        logger.warning(f"Error extracting microdata property: {str(e)}")
                        continue
                if item_data['properties']:  # Only add if has properties
                    structured_data['microdata'].append(item_data)
            except Exception as e:
                logger.warning(f"Error processing microdata item: {str(e)}")
                continue
    except Exception as e:
        logger.warning(f"Error extracting microdata: {str(e)}")
    
    # Extract comprehensive meta tags
    try:
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            try:
                # Handle different meta tag formats safely
                name_attr = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content_attr = meta.get('content')
                if name_attr and content_attr:
                    structured_data['meta_tags'].append({'name': str(name_attr), 'content': str(content_attr)})
            except Exception as e:
                logger.warning(f"Error processing meta tag: {str(e)}")
                continue
    except Exception as e:
        logger.warning(f"Error extracting meta tags: {str(e)}")
    
    # Extract social media metadata with error handling
    try:
        social_tags = {
            'og:title': soup.find('meta', property='og:title'),
            'og:description': soup.find('meta', property='og:description'), 
            'og:image': soup.find('meta', property='og:image'),
            'og:url': soup.find('meta', property='og:url'),
            'og:type': soup.find('meta', property='og:type'),
            'twitter:card': soup.find('meta', attrs={'name': 'twitter:card'}),
            'twitter:title': soup.find('meta', attrs={'name': 'twitter:title'}),
            'twitter:description': soup.find('meta', attrs={'name': 'twitter:description'}),
            'twitter:image': soup.find('meta', attrs={'name': 'twitter:image'})
        }
        
        for key, tag in social_tags.items():
            try:
                if tag and tag.get('content'):
                    structured_data['social_media'][key] = str(tag.get('content', ''))
            except Exception as e:
                logger.warning(f"Error processing social media tag {key}: {str(e)}")
                continue
    except Exception as e:
        logger.warning(f"Error extracting social media data: {str(e)}")
    
    # Extract contact information with error handling
    try:
        page_text = soup.get_text()
        contact_patterns = {
            'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text),
            'phones': re.findall(r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', page_text)
        }
        # Remove duplicates and limit results
        contact_patterns['emails'] = list(set(contact_patterns['emails']))[:10]
        contact_patterns['phones'] = list(set(contact_patterns['phones']))[:10]
        structured_data['contact_info'] = contact_patterns
    except Exception as e:
        logger.warning(f"Error extracting contact information: {str(e)}")
        structured_data['contact_info'] = {'emails': [], 'phones': []}
    
    # Extract forms with error handling
    try:
        forms = soup.find_all('form')
        for form in forms:
            try:
                form_data = {
                    'action': str(form.get('action', '')),
                    'method': str(form.get('method', 'GET')),
                    'inputs': []
                }
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_elem in inputs:
                    try:
                        input_data = {
                            'type': str(input_elem.get('type', input_elem.name)),
                            'name': str(input_elem.get('name', '')),
                            'id': str(input_elem.get('id', '')),
                            'placeholder': str(input_elem.get('placeholder', '')),
                            'required': input_elem.has_attr('required')
                        }
                        form_data['inputs'].append(input_data)
                    except Exception as e:
                        logger.warning(f"Error processing form input: {str(e)}")
                        continue
                structured_data['forms'].append(form_data)
            except Exception as e:
                logger.warning(f"Error processing form: {str(e)}")
                continue
    except Exception as e:
        logger.warning(f"Error extracting forms: {str(e)}")
    
    # Extract media elements with error handling
    try:
        media_elements = {
            'videos': soup.find_all('video'),
            'audios': soup.find_all('audio'),
            'iframes': soup.find_all('iframe')
        }
        
        for media_type, elements in media_elements.items():
            media_list = []
            for elem in elements[:10]:  # Limit to 10 per type
                try:
                    media_info = {
                        'src': str(elem.get('src', '')),
                        'title': str(elem.get('title', '')),
                        'alt': str(elem.get('alt', '')),
                        'width': str(elem.get('width', '')),
                        'height': str(elem.get('height', ''))
                    }
                    media_list.append(media_info)
                except Exception as e:
                    logger.warning(f"Error processing {media_type} element: {str(e)}")
                    continue
            if media_list:  # Only add if we have media items
                structured_data['media'].append({media_type: media_list})
    except Exception as e:
        logger.warning(f"Error extracting media elements: {str(e)}")
    
    return structured_data

def extract_advanced_content(soup):
    """Extract advanced content structures"""
    content_data = {
        'navigation': [],
        'breadcrumbs': [],
        'lists': [],
        'code_blocks': [],
        'quotes': [],
        'data_attributes': []
    }
    
    # Extract navigation
    nav_elements = soup.find_all(['nav', 'ul', 'ol'])
    for nav in nav_elements:
        if nav.name == 'nav' or 'nav' in nav.get('class', []):
            links = nav.find_all('a')
            nav_items = []
            for link in links:
                nav_items.append({
                    'text': link.get_text().strip(),
                    'href': link.get('href', ''),
                    'title': link.get('title', '')
                })
            content_data['navigation'].append(nav_items)
    
    # Extract breadcrumbs
    breadcrumb_selectors = [
        '[class*="breadcrumb"]',
        '[id*="breadcrumb"]',
        '.breadcrumbs',
        'nav[aria-label*="breadcrumb" i]'
    ]
    
    for selector in breadcrumb_selectors:
        breadcrumbs = soup.select(selector)
        for breadcrumb in breadcrumbs:
            links = breadcrumb.find_all('a')
            breadcrumb_items = []
            for link in links:
                breadcrumb_items.append({
                    'text': link.get_text().strip(),
                    'href': link.get('href', '')
                })
            if breadcrumb_items:
                content_data['breadcrumbs'].append(breadcrumb_items)
    
    # Extract lists
    lists = soup.find_all(['ul', 'ol', 'dl'])
    for list_elem in lists[:10]:  # Limit to first 10 lists
        list_items = []
        if list_elem.name in ['ul', 'ol']:
            items = list_elem.find_all('li')
            for item in items:
                list_items.append(item.get_text().strip())
        else:  # dl (description list)
            dts = list_elem.find_all('dt')
            dds = list_elem.find_all('dd')
            for dt, dd in zip(dts, dds):
                list_items.append({
                    'term': dt.get_text().strip(),
                    'description': dd.get_text().strip()
                })
        
        if list_items:
            content_data['lists'].append({
                'type': list_elem.name,
                'items': list_items
            })
    
    # Extract code blocks
    code_elements = soup.find_all(['code', 'pre'])
    for code in code_elements[:10]:  # Limit to first 10 code blocks
        content_data['code_blocks'].append({
            'tag': code.name,
            'content': code.get_text().strip(),
            'language': code.get('class', [''])[0] if code.get('class') else ''
        })
    
    # Extract quotes
    quote_elements = soup.find_all(['blockquote', 'q'])
    for quote in quote_elements:
        content_data['quotes'].append({
            'text': quote.get_text().strip(),
            'cite': quote.get('cite', ''),
            'author': quote.get('data-author', '')
        })
    
    # Extract elements with data attributes
    data_elements = soup.find_all(attrs=lambda x: x and any(key.startswith('data-') for key in x))
    for elem in data_elements[:20]:  # Limit to first 20 elements
        data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
        if data_attrs:
            content_data['data_attributes'].append({
                'tag': elem.name,
                'text': elem.get_text().strip()[:100] + '...' if len(elem.get_text().strip()) > 100 else elem.get_text().strip(),
                'data_attributes': data_attrs
            })
    
    return content_data

def extract_seo_data(soup):
    """Extract SEO-related data"""
    seo_data = {
        'title_tag': '',
        'meta_description': '',
        'meta_keywords': '',
        'canonical_url': '',
        'robots': '',
        'lang': '',
        'hreflang': [],
        'schema_markup': [],
        'heading_structure': {},
        'internal_links': 0,
        'external_links': 0,
        'images_without_alt': 0,
        'page_load_hints': []
    }
    
    # Basic SEO tags
    title = soup.find('title')
    seo_data['title_tag'] = title.get_text().strip() if title else ''
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    seo_data['meta_description'] = meta_desc.get('content', '') if meta_desc else ''
    
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    seo_data['meta_keywords'] = meta_keywords.get('content', '') if meta_keywords else ''
    
    canonical = soup.find('link', rel='canonical')
    seo_data['canonical_url'] = canonical.get('href', '') if canonical else ''
    
    robots = soup.find('meta', attrs={'name': 'robots'})
    seo_data['robots'] = robots.get('content', '') if robots else ''
    
    # Language attributes
    html = soup.find('html')
    seo_data['lang'] = html.get('lang', '') if html else ''
    
    # Hreflang
    hreflang_links = soup.find_all('link', rel='alternate', hreflang=True)
    for link in hreflang_links:
        seo_data['hreflang'].append({
            'hreflang': link.get('hreflang'),
            'href': link.get('href')
        })
    
    # Heading structure analysis
    for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        headings = soup.find_all(level)
        seo_data['heading_structure'][level] = len(headings)
    
    # Link analysis
    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        if href.startswith(('http://', 'https://')):
            seo_data['external_links'] += 1
        elif href.startswith(('/', '#')):
            seo_data['internal_links'] += 1
    
    # Image analysis
    images = soup.find_all('img')
    seo_data['images_without_alt'] = len([img for img in images if not img.get('alt')])
    
    # Performance hints
    preload_links = soup.find_all('link', rel='preload')
    prefetch_links = soup.find_all('link', rel='prefetch')
    seo_data['page_load_hints'] = {
        'preload': len(preload_links),
        'prefetch': len(prefetch_links)
    }
    
    return seo_data

def extract_data_from_url(url):
    """Extract comprehensive structured data from a given URL"""
    try:
        # Enhanced headers to avoid bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Create a session for better handling
        session = requests.Session()
        session.headers.update(headers)
        
        # Add delay to avoid rate limiting
        import time
        time.sleep(1)
        
        # Try multiple approaches if first fails
        response = None
        error_messages = []
        
        # Attempt 1: Standard request
        try:
            response = session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_messages.append(f"HTTP Error: {e}")
            
            # Attempt 2: Try with different User-Agent
            if response and response.status_code == 403:
                logger.info("403 error, trying with different User-Agent")
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
                })
                try:
                    time.sleep(2)  # Longer delay
                    response = session.get(url, timeout=30)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e2:
                    error_messages.append(f"Second attempt HTTP Error: {e2}")
                    
                    # Attempt 3: Try with minimal headers
                    session.headers.clear()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (compatible; WebScraper/1.0; +http://example.com/bot)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    })
                    try:
                        time.sleep(3)  # Even longer delay
                        response = session.get(url, timeout=30)
                        response.raise_for_status()
                    except Exception as e3:
                        error_messages.append(f"Third attempt Error: {e3}")
                        raise e3
        
        if not response or response.status_code != 200:
            error_msg = f"Failed to fetch URL after multiple attempts. Errors: {'; '.join(error_messages)}"
            return {'error': error_msg}
        
        # Check if we got actual HTML content
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml' not in content_type:
            return {'error': f"Response is not HTML content. Content-Type: {content_type}"}
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we got a valid page (not an error page)
        if soup.find('title'):
            title_text = soup.find('title').get_text().strip().lower()
            if any(error_term in title_text for error_term in ['403', 'forbidden', 'access denied', 'blocked', 'error']):
                return {'error': f"Page appears to be an error page. Title: {title_text}"}
        
        # Extract basic information with error handling
        try:
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"
        except Exception as e:
            logger.warning(f"Error extracting title: {str(e)}")
            title_text = "No title found"
        
        # Extract meta description with error handling
        try:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else "No description found"
        except Exception as e:
            logger.warning(f"Error extracting description: {str(e)}")
            description = "No description found"
        
        # Extract all headings with hierarchy and error handling
        headings = []
        heading_hierarchy = {}
        try:
            for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                try:
                    level_headings = soup.find_all(level)
                    heading_hierarchy[level] = len(level_headings)
                    for heading in level_headings:
                        try:
                            headings.append({
                                'level': level,
                                'text': heading.get_text().strip()[:500],  # Limit text length
                                'id': str(heading.get('id', '')),
                                'class': ' '.join(heading.get('class', []))
                            })
                        except Exception as e:
                            logger.warning(f"Error processing heading {level}: {str(e)}")
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting {level} headings: {str(e)}")
                    heading_hierarchy[level] = 0
        except Exception as e:
            logger.warning(f"Error extracting headings: {str(e)}")
        
        # Extract all links with enhanced data and error handling
        links = []
        try:
            all_links = soup.find_all('a', href=True)
            for link in all_links[:500]:  # Limit to 500 links
                try:
                    link_href = str(link['href'])
                    link_data = {
                        'text': link.get_text().strip()[:200],  # Limit text length
                        'url': link_href,
                        'title': str(link.get('title', '')),
                        'target': str(link.get('target', '')),
                        'rel': ' '.join(link.get('rel', [])),
                        'class': ' '.join(link.get('class', [])),
                        'is_external': link_href.startswith(('http://', 'https://')) and urlparse(url).netloc not in link_href
                    }
                    links.append(link_data)
                except Exception as e:
                    logger.warning(f"Error processing link: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error extracting links: {str(e)}")
        
        # Extract all images with enhanced data and error handling
        images = []
        try:
            all_images = soup.find_all('img')
            for img in all_images[:200]:  # Limit to 200 images
                try:
                    img_src = img.get('src', img.get('data-src', ''))
                    if img_src:
                        img_data = {
                            'alt': str(img.get('alt', '')),
                            'src': urljoin(url, str(img_src)),
                            'title': str(img.get('title', '')),
                            'width': str(img.get('width', '')),
                            'height': str(img.get('height', '')),
                            'loading': str(img.get('loading', '')),
                            'class': ' '.join(img.get('class', []))
                        }
                        images.append(img_data)
                except Exception as e:
                    logger.warning(f"Error processing image: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error extracting images: {str(e)}")
        
        # Extract text content (cleaned) with error handling
        try:
            text_content = soup.get_text()
            text_content = re.sub(r'\s+', ' ', text_content).strip()
        except Exception as e:
            logger.warning(f"Error extracting text content: {str(e)}")
            text_content = "Error extracting text content"
        
        # Enhanced table extraction with error handling
        tables = []
        table_summaries = []
        try:
            all_tables = soup.find_all('table')
            for i, table in enumerate(all_tables[:20]):  # Limit to 20 tables
                try:
                    rows = []
                    headers = []
                    
                    # Try to find headers
                    header_row = table.find('tr')
                    if header_row and header_row.find('th'):
                        try:
                            headers = [th.get_text().strip() for th in header_row.find_all('th')]
                        except Exception as e:
                            logger.warning(f"Error extracting table headers: {str(e)}")
                    
                    # Extract all rows
                    for row in table.find_all('tr'):
                        try:
                            cells = []
                            for cell in row.find_all(['td', 'th']):
                                try:
                                    cell_text = re.sub(r'\s+', ' ', cell.get_text().strip())
                                    cells.append(cell_text[:100])  # Limit cell text length
                                except Exception as e:
                                    cells.append("")
                            if cells and any(cell for cell in cells):
                                rows.append(cells)
                        except Exception as e:
                            logger.warning(f"Error processing table row: {str(e)}")
                            continue
                    
                    if rows:
                        # Create DataFrame
                        try:
                            if headers and len(headers) == len(rows[0]):
                                df = pd.DataFrame(rows[1:] if table.find('th') else rows, columns=headers)
                            else:
                                df = pd.DataFrame(rows)
                            
                            # Clean DataFrame
                            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
                            
                            tables.append(df.to_dict('records'))
                            table_summaries.append({
                                'table_id': i + 1,
                                'rows': len(df),
                                'columns': len(df.columns),
                                'headers': list(df.columns) if headers else [f'Column_{i+1}' for i in range(len(df.columns))],
                                'has_headers': bool(headers),
                                'caption': table.find('caption').get_text().strip() if table.find('caption') else ''
                            })
                        except Exception as e:
                            logger.warning(f"Error processing table data: {str(e)}")
                            continue
                except Exception as e:
                    logger.warning(f"Error processing table {i}: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        
        # Extract advanced structures with error handling
        try:
            structured_data = extract_structured_data(soup, url)
        except Exception as e:
            logger.warning(f"Error extracting structured data: {str(e)}")
            structured_data = {'json_ld': [], 'microdata': [], 'meta_tags': [], 'social_media': {}, 'contact_info': {}, 'forms': [], 'media': []}
        
        try:
            content_data = extract_advanced_content(soup)
        except Exception as e:
            logger.warning(f"Error extracting content data: {str(e)}")
            content_data = {'navigation': [], 'breadcrumbs': [], 'lists': [], 'code_blocks': [], 'quotes': [], 'data_attributes': []}
        
        try:
            seo_data = extract_seo_data(soup)
        except Exception as e:
            logger.warning(f"Error extracting SEO data: {str(e)}")
            seo_data = {}
        
        return {
            'url': url,
            'title': title_text,
            'description': description,
            'headings': headings,
            'heading_hierarchy': heading_hierarchy,
            'links': links,
            'images': images,
            'text_content': text_content[:5000] + '...' if len(text_content) > 5000 else text_content,
            'word_count': len(text_content.split()),
            'tables': tables,
            'table_summaries': table_summaries,
            'structured_data': structured_data,
            'content_data': content_data,
            'seo_data': seo_data,
            'scraped_at': datetime.now().isoformat(),
            'response_status': response.status_code,
            'response_headers': dict(response.headers),
            'page_size_bytes': len(response.content)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return {'error': f"Failed to fetch URL: {str(e)}. This might be due to anti-bot protection, rate limiting, or server restrictions."}
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        return {'error': f"Error processing content: {str(e)}"}

def generate_comprehensive_csv_files(data):
    """Generate multiple CSV files for different data types with enhanced accuracy"""
    if 'error' in data:
        return {'error': data['error']}
    
    csv_files = {}
    
    try:
        # 1. Enhanced main summary data
        extraction_stats = data.get('extraction_stats', {})
        main_data = {
            'URL': [data['url']],
            'Final_URL': [data.get('final_url', data['url'])],
            'Title': [data['title']],
            'Title_Length': [len(data.get('title', ''))],
            'Description': [data['description']],
            'Description_Length': [len(data.get('description', ''))],
            'Word_Count': [data.get('word_count', 0)],
            'Sentence_Count': [data.get('sentence_count', 0)],
            'Paragraph_Count': [data.get('paragraph_count', 0)],
            'Character_Count': [data.get('character_count', 0)],
            'Reading_Time_Minutes': [data.get('reading_time_minutes', 0)],
            'Page_Size_Bytes': [data.get('page_size_bytes', 0)],
            'Load_Time_Seconds': [data.get('load_time_seconds', 0)],
            'Response_Status': [data.get('response_status', 0)],
            'Total_Headings': [extraction_stats.get('total_headings', 0)],
            'Total_Links': [extraction_stats.get('total_links', 0)],
            'Total_Images': [extraction_stats.get('total_images', 0)],
            'Total_Tables': [extraction_stats.get('total_tables', 0)],
            'Internal_Links': [extraction_stats.get('internal_links', 0)],
            'External_Links': [extraction_stats.get('external_links', 0)],
            'Images_With_Alt': [extraction_stats.get('images_with_alt', 0)],
            'Images_Without_Alt': [extraction_stats.get('images_without_alt', 0)],
            'Scraped_At': [data.get('scraped_at', '')]
        }
        
        # Add detailed heading counts
        heading_hierarchy = data.get('heading_hierarchy', {})
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            main_data[f'{level.upper()}_Count'] = [heading_hierarchy.get(level, 0)]
        
        csv_files['main_summary'] = pd.DataFrame(main_data).to_csv(index=False)
        
        # 2. Enhanced headings data
        if data.get('headings'):
            headings_data = []
            for heading in data['headings']:
                headings_data.append({
                    'URL': data['url'],
                    'Level': heading.get('level', ''),
                    'Text': heading.get('text', ''),
                    'Text_Length': len(heading.get('text', '')),
                    'ID': heading.get('id', ''),
                    'Class': heading.get('class', ''),
                    'Position': heading.get('position', 0),
                    'Has_ID': bool(heading.get('id', '')),
                    'Has_Class': bool(heading.get('class', ''))
                })
            csv_files['headings'] = pd.DataFrame(headings_data).to_csv(index=False)
        
        # 3. Enhanced links data
        if data.get('links'):
            links_data = []
            for link in data['links']:
                links_data.append({
                    'URL': data['url'],
                    'Link_Text': link.get('text', ''),
                    'Link_URL': link.get('url', ''),
                    'Resolved_URL': link.get('resolved_url', ''),
                    'Title': link.get('title', ''),
                    'Target': link.get('target', ''),
                    'Rel': link.get('rel', ''),
                    'Class': link.get('class', ''),
                    'Is_External': link.get('is_external', False),
                    'Position': link.get('position', 0),
                    'Text_Length': len(link.get('text', '')),
                    'Has_Title': bool(link.get('title', '')),
                    'Opens_New_Tab': link.get('target', '') == '_blank'
                })
            csv_files['links'] = pd.DataFrame(links_data).to_csv(index=False)
        
        # 4. Enhanced images data
        if data.get('images'):
            images_data = []
            for img in data['images']:
                images_data.append({
                    'URL': data['url'],
                    'Alt_Text': img.get('alt', ''),
                    'Image_Src': img.get('src', ''),
                    'Resolved_Src': img.get('resolved_src', ''),
                    'Title': img.get('title', ''),
                    'Width': img.get('width', ''),
                    'Height': img.get('height', ''),
                    'Loading': img.get('loading', ''),
                    'Class': img.get('class', ''),
                    'Position': img.get('position', 0),
                    'Has_Alt': img.get('has_alt', False),
                    'Alt_Length': len(img.get('alt', '')),
                    'Has_Dimensions': bool(img.get('width') or img.get('height')),
                    'Is_Lazy_Loaded': img.get('loading', '') == 'lazy'
                })
            csv_files['images'] = pd.DataFrame(images_data).to_csv(index=False)
        
        # 5. Enhanced SEO analysis
        seo_data = data.get('seo_data', {})
        if seo_data:
            seo_analysis_data = []
            seo_record = {
                'URL': data['url'],
                'Title_Tag': seo_data.get('title_tag', ''),
                'Title_Length': len(seo_data.get('title_tag', '')),
                'Title_Optimal': 30 <= len(seo_data.get('title_tag', '')) <= 60,
                'Meta_Description': seo_data.get('meta_description', ''),
                'Description_Length': len(seo_data.get('meta_description', '')),
                'Description_Optimal': 120 <= len(seo_data.get('meta_description', '')) <= 160,
                'Meta_Keywords': seo_data.get('meta_keywords', ''),
                'Canonical_URL': seo_data.get('canonical_url', ''),
                'Has_Canonical': bool(seo_data.get('canonical_url', '')),
                'Robots': seo_data.get('robots', ''),
                'Language': seo_data.get('lang', ''),
                'Internal_Links': seo_data.get('internal_links', 0),
                'External_Links': seo_data.get('external_links', 0),
                'Images_Without_Alt': seo_data.get('images_without_alt', 0),
                'SEO_Score': calculate_seo_score(seo_data, data)
            }
            
            # Add heading structure
            heading_structure = seo_data.get('heading_structure', {})
            for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                seo_record[f'{level.upper()}_Count'] = heading_structure.get(level, 0)
            
            seo_analysis_data.append(seo_record)
            csv_files['seo_analysis'] = pd.DataFrame(seo_analysis_data).to_csv(index=False)
        
        # 6. Enhanced meta tags
        meta_tags = data.get('structured_data', {}).get('meta_tags', [])
        if meta_tags:
            meta_data = []
            for tag in meta_tags:
                meta_data.append({
                    'URL': data['url'],
                    'Name': tag.get('name', ''),
                    'Content': tag.get('content', ''),
                    'Content_Length': len(tag.get('content', '')),
                    'Is_SEO_Related': tag.get('name', '').lower() in ['description', 'keywords', 'robots', 'author', 'viewport'],
                    'Is_Social_Media': tag.get('name', '').lower().startswith(('og:', 'twitter:', 'fb:'))
                })
            csv_files['meta_tags'] = pd.DataFrame(meta_data).to_csv(index=False)
        
        # 7. Enhanced social media data
        social_media = data.get('structured_data', {}).get('social_media', {})
        if social_media:
            social_data = []
            for key, value in social_media.items():
                if value:
                    platform = 'Open_Graph' if key.startswith('og:') else 'Twitter'
                    property_name = key.split(':', 1)[1] if ':' in key else key
                    social_data.append({
                        'URL': data['url'],
                        'Platform': platform,
                        'Property': property_name,
                        'Content': value,
                        'Content_Length': len(value),
                        'Is_Image': property_name == 'image',
                        'Is_Title': property_name == 'title',
                        'Is_Description': property_name == 'description'
                    })
            if social_data:
                csv_files['social_media'] = pd.DataFrame(social_data).to_csv(index=False)
        
        # 8. Enhanced contact information
        contact_info = data.get('structured_data', {}).get('contact_info', {})
        if contact_info.get('emails') or contact_info.get('phones'):
            contact_data = []
            for email in contact_info.get('emails', []):
                contact_data.append({
                    'URL': data['url'],
                    'Type': 'Email',
                    'Value': email,
                    'Domain': email.split('@')[1] if '@' in email else '',
                    'Is_Generic': any(generic in email.lower() for generic in ['info@', 'contact@', 'support@', 'admin@'])
                })
            for phone in contact_info.get('phones', []):
                contact_data.append({
                    'URL': data['url'],
                    'Type': 'Phone',
                    'Value': phone,
                    'Domain': '',
                    'Is_Generic': False
                })
            if contact_data:
                csv_files['contact_info'] = pd.DataFrame(contact_data).to_csv(index=False)
        
        # 9. Enhanced forms data
        forms = data.get('structured_data', {}).get('forms', [])
        if forms:
            forms_data = []
            for i, form in enumerate(forms):
                inputs = form.get('inputs', [])
                forms_data.append({
                    'URL': data['url'],
                    'Form_ID': i + 1,
                    'Action': form.get('action', ''),
                    'Method': form.get('method', 'GET'),
                    'Input_Count': len(inputs),
                    'Has_Action': bool(form.get('action', '')),
                    'Is_Search_Form': 'search' in form.get('action', '').lower(),
                    'Is_Contact_Form': any(inp.get('type') == 'email' or 'email' in inp.get('name', '').lower() for inp in inputs),
                    'Required_Fields': sum(1 for inp in inputs if inp.get('required', False)),
                    'Text_Inputs': sum(1 for inp in inputs if inp.get('type') in ['text', 'email', 'tel', 'url']),
                    'Has_Submit': any(inp.get('type') == 'submit' for inp in inputs)
                })
            csv_files['forms_summary'] = pd.DataFrame(forms_data).to_csv(index=False)
        
        # 10. Enhanced content structure
        lists_data = data.get('content_data', {}).get('lists', [])
        if lists_data:
            lists_summary = []
            for i, list_item in enumerate(lists_data):
                items = list_item.get('items', [])
                lists_summary.append({
                    'URL': data['url'],
                    'List_ID': i + 1,
                    'Type': list_item.get('type', ''),
                    'Item_Count': len(items),
                    'Is_Ordered': list_item.get('type') == 'ol',
                    'Is_Definition': list_item.get('type') == 'dl',
                    'Average_Item_Length': sum(len(str(item)) for item in items) / len(items) if items else 0,
                    'Has_Long_Items': any(len(str(item)) > 100 for item in items)
                })
            csv_files['lists_summary'] = pd.DataFrame(lists_summary).to_csv(index=False)
        
        # 11. Individual table files with enhanced structure
        tables = data.get('tables', [])
        table_summaries = data.get('table_summaries', [])
        for i, (table, summary) in enumerate(zip(tables, table_summaries)):
            if table:
                try:
                    df = pd.DataFrame(table)
                    if not df.empty:
                        # Add metadata columns
                        df['Source_URL'] = data['url']
                        df['Table_ID'] = summary.get('table_id', i + 1)
                        df['Row_Number'] = range(1, len(df) + 1)
                        csv_files[f'table_{i+1}'] = df.to_csv(index=False)
                except Exception as e:
                    logger.warning(f"Error creating CSV for table {i+1}: {str(e)}")
        
        # 12. Enhanced full text content with analysis
        if data.get('text_content'):
            text_data = {
                'URL': [data['url']],
                'Full_Text_Content': [data['text_content']],
                'Word_Count': [data.get('word_count', 0)],
                'Character_Count': [data.get('character_count', 0)],
                'Sentence_Count': [data.get('sentence_count', 0)],
                'Paragraph_Count': [data.get('paragraph_count', 0)],
                'Reading_Time_Minutes': [data.get('reading_time_minutes', 0)],
                'Average_Words_Per_Sentence': [data.get('word_count', 0) / max(data.get('sentence_count', 1), 1)],
                'Average_Sentence_Per_Paragraph': [data.get('sentence_count', 0) / max(data.get('paragraph_count', 1), 1)]
            }
            csv_files['full_text_content'] = pd.DataFrame(text_data).to_csv(index=False)
        
        # 13. Performance and technical metrics
        performance_data = {
            'URL': [data['url']],
            'Final_URL': [data.get('final_url', data['url'])],
            'Response_Status': [data.get('response_status', 0)],
            'Page_Size_Bytes': [data.get('page_size_bytes', 0)],
            'Page_Size_KB': [data.get('page_size_bytes', 0) / 1024],
            'Load_Time_Seconds': [data.get('load_time_seconds', 0)],
            'Content_Type': [data.get('response_headers', {}).get('content-type', '')],
            'Server': [data.get('response_headers', {}).get('server', '')],
            'Is_Redirected': [data['url'] != data.get('final_url', data['url'])],
            'Has_Cache_Headers': [bool(data.get('response_headers', {}).get('cache-control') or data.get('response_headers', {}).get('expires'))],
            'Is_Compressed': ['gzip' in data.get('response_headers', {}).get('content-encoding', '')],
            'Scraped_At': [data.get('scraped_at', '')]
        }
        csv_files['performance_metrics'] = pd.DataFrame(performance_data).to_csv(index=False)
        
        return {'csv_files': csv_files}
        
    except Exception as e:
        logger.error(f"Error generating CSV files: {str(e)}")
        return {'error': f'Error generating CSV files: {str(e)}'}

def calculate_seo_score(seo_data, full_data):
    """Calculate a comprehensive SEO score (0-100)"""
    score = 0
    max_score = 100
    
    try:
        # Title optimization (20 points)
        title_length = len(seo_data.get('title_tag', ''))
        if title_length == 0:
            score += 0
        elif 30 <= title_length <= 60:
            score += 20
        elif 20 <= title_length <= 80:
            score += 15
        else:
            score += 5
        
        # Meta description (20 points)
        desc_length = len(seo_data.get('meta_description', ''))
        if desc_length == 0:
            score += 0
        elif 120 <= desc_length <= 160:
            score += 20
        elif 100 <= desc_length <= 200:
            score += 15
        else:
            score += 5
        
        # Heading structure (20 points)
        heading_structure = seo_data.get('heading_structure', {})
        h1_count = heading_structure.get('h1', 0)
        h2_count = heading_structure.get('h2', 0)
        
        if h1_count == 1:
            score += 10
        elif h1_count > 1:
            score += 5
        
        if h2_count > 0:
            score += 10
        
        # Image optimization (15 points)
        images_without_alt = seo_data.get('images_without_alt', 0)
        total_images = full_data.get('extraction_stats', {}).get('total_images', 0)
        if total_images > 0:
            alt_ratio = (total_images - images_without_alt) / total_images
            score += int(15 * alt_ratio)
        else:
            score += 15  # No images to optimize
        
        # Content length (10 points)
        word_count = full_data.get('word_count', 0)
        if word_count >= 300:
            score += 10
        elif word_count >= 150:
            score += 7
        elif word_count >= 50:
            score += 3
        
        # Internal linking (10 points)
        internal_links = seo_data.get('internal_links', 0)
        if internal_links >= 3:
            score += 10
        elif internal_links >= 1:
            score += 7
        
        # Technical SEO (5 points)
        if seo_data.get('canonical_url'):
            score += 2.5
        if seo_data.get('lang'):
            score += 2.5
        
    except Exception as e:
        logger.warning(f"Error calculating SEO score: {str(e)}")
        return 0
    
    return min(score, max_score)

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        url = body.get('url')
        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({'error': 'URL is required'})
            }
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Extract comprehensive data
        raw_data = extract_data_from_url(url)
        
        if 'error' in raw_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps(raw_data)
            }
        
        # Generate CSV files
        csv_result = generate_comprehensive_csv_files(raw_data)
        
        # Prepare response data (limit size for response)
        response_data = {
            'url': raw_data['url'],
            'title': raw_data['title'],
            'description': raw_data['description'],
            'word_count': raw_data.get('word_count', 0),
            'page_size_bytes': raw_data.get('page_size_bytes', 0),
            'total_headings': len(raw_data.get('headings', [])),
            'total_links': len(raw_data.get('links', [])),
            'total_images': len(raw_data.get('images', [])),
            'total_tables': len(raw_data.get('tables', [])),
            'heading_hierarchy': raw_data.get('heading_hierarchy', {}),
            'scraped_at': raw_data.get('scraped_at', ''),
            'seo_summary': {
                'internal_links': raw_data.get('seo_data', {}).get('internal_links', 0),
                'external_links': raw_data.get('seo_data', {}).get('external_links', 0),
                'images_without_alt': raw_data.get('seo_data', {}).get('images_without_alt', 0),
                'title_length': len(raw_data.get('seo_data', {}).get('title_tag', '')),
                'description_length': len(raw_data.get('seo_data', {}).get('meta_description', ''))
            },
            'available_files': list(csv_result['csv_files'].keys()) if 'csv_files' in csv_result else []
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': response_data,
                'full_data': raw_data,  # Include full data for detailed analysis
                'csv_files': csv_result.get('csv_files', {})
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }