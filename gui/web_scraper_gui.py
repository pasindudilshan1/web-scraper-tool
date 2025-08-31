import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import json
import threading
import os
from datetime import datetime
import webbrowser
from urllib.parse import urlparse

class EnhancedWebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(" Web Scraper Tool")
        # Recommended screen size
        recommended_width = 1280
        recommended_height = 900
        self.root.geometry(f"{recommended_width}x{recommended_height}")
        self.root.minsize(1000, 700)
        # Center window on screen
        self.center_window(recommended_width, recommended_height)
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width // 2) - (width // 2))
        y = max(0, (screen_height // 2) - (height // 2))
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure style
        self.setup_styles()
        
        # AWS Lambda API endpoint
        self.lambda_endpoint = "EnterEndPOint"
        
        # Data storage
        self.scraped_data = {}
        self.csv_files = {}
        self.full_data = {}
        
        # Create GUI elements
        self.create_widgets()
        
    def setup_styles(self):
        """Configure ttk styles for better appearance"""
        style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'bg': '#f5f5f5',
            'fg': '#333333',
            'accent': '#0078d4',
            'success': '#107c10',
            'error': '#d13438',
            'warning': '#ff8c00',
            'info': '#005a9e'
        }
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Custom button styles
        style.configure('Accent.TButton', foreground='red', background=self.colors['accent'])
        style.configure('Success.TButton', foreground='white', background=self.colors['success'])
        style.configure('Warning.TButton', foreground='white', background=self.colors['warning'])
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Create main container with scrollable frame
        self.create_main_container()
        
        # Title section
        self.create_title_section()
        
        # URL Input section
        self.create_url_section()
        
        # Control buttons section
        self.create_control_buttons()
        
        # Progress section
        self.create_progress_section()
        
        # Results tabs section
        self.create_results_tabs()
        
        # Download section
        self.create_download_section()
        
        # Status bar
        self.create_status_bar()
        
    def create_main_container(self):
        """Create main scrollable container"""
        # Main frame with scrollbar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        
    def create_title_section(self):
        """Create title and description section"""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        title_frame.columnconfigure(0, weight=1)
        
        # Main title
        title_label = ttk.Label(title_frame, text="🕷️ Enhanced Web Scraper Tool", 
                               font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(title_frame, 
                                  text="Extract comprehensive data from any website including SEO, structured data, and content analysis",
                                  font=('Arial', 11), foreground=self.colors['info'])
        subtitle_label.grid(row=1, column=0)
        
    def create_url_section(self):
        """Create URL input section"""
        url_frame = ttk.LabelFrame(self.main_frame, text="🌐 Website URL", padding="15")
        url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="Enter URL to scrape:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        self.url_entry = ttk.Entry(url_frame, width=60, font=('Arial', 11))
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(8, 10))
        self.url_entry.insert(0, "https://")
        
        # URL validation indicator
        self.url_status_label = ttk.Label(url_frame, text="", font=('Arial', 9))
        self.url_status_label.grid(row=2, column=0, columnspan=3, sticky=tk.W)
        
        # Bind URL validation
        self.url_entry.bind('<KeyRelease>', self.validate_url)
        
        # Quick examples
        examples_frame = ttk.Frame(url_frame)
        examples_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Label(examples_frame, text="Quick Examples:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        Try = [
            ("News Site", "https://news.ycombinator.com"),
            ("E-commerce", "https://example-store.com"),
            ("Blog", "https://medium.com"),
            ("Documentation", "https://docs.python.org")
        ]
        
        for label, url in Try:
            btn = ttk.Button(examples_frame, text=label, 
                           command=lambda u=url: self.set_url(u),
                           style='TButton')
            btn.pack(side=tk.LEFT, padx=5)
            
    def create_control_buttons(self):
        """Create control buttons section"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 15))
        
        self.scrape_button = ttk.Button(button_frame, text="🚀 Start Advanced Scraping", 
                                       command=self.start_scraping, 
                                       style='Accent.TButton',
                                       width=25)
        self.scrape_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.analyze_button = ttk.Button(button_frame, text="📊 Analyze Results", 
                                        command=self.analyze_results,
                                        state=tk.DISABLED,
                                        width=20)
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear All", 
                                     command=self.clear_all,
                                     width=15)
        self.clear_button.pack(side=tk.LEFT)
        
    def create_progress_section(self):
        """Create progress indicators section"""
        progress_frame = ttk.LabelFrame(self.main_frame, text="📈 Progress", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="Ready to scrape...", font=('Arial', 10))
        self.progress_label.grid(row=1, column=0)
        
        # Time estimation
        self.time_label = ttk.Label(progress_frame, text="", font=('Arial', 9), foreground=self.colors['info'])
        self.time_label.grid(row=2, column=0, pady=(5, 0))
        
    def create_results_tabs(self):
        """Create results display tabs"""
        results_frame = ttk.LabelFrame(self.main_frame, text="📋 Scraping Results", padding="10")
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Configure main frame row weight
        self.main_frame.rowconfigure(4, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_summary_tab()
        self.create_seo_tab()
        self.create_content_tab()
        self.create_links_tab()
        self.create_images_tab()
        self.create_tables_tab()
        self.create_structured_data_tab()
        self.create_raw_data_tab()
        
    def create_summary_tab(self):
        """Create summary overview tab"""
        self.summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.summary_frame, text="📊 Summary")
        
        self.summary_text = scrolledtext.ScrolledText(
            self.summary_frame, height=20, width=80, wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
    def create_seo_tab(self):
        """Create SEO analysis tab"""
        self.seo_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.seo_frame, text="🔍 SEO Analysis")
        
        self.seo_text = scrolledtext.ScrolledText(
            self.seo_frame, height=20, width=80, wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.seo_text.pack(fill=tk.BOTH, expand=True)
        
    def create_content_tab(self):
        """Create content analysis tab"""
        self.content_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.content_frame, text="📝 Content")
        
        # Create treeview for structured content display
        columns = ('Type', 'Count', 'Details')
        self.content_tree = ttk.Treeview(self.content_frame, columns=columns, show='tree headings', height=15)
        
        # Configure columns
        self.content_tree.heading('#0', text='Content Element')
        self.content_tree.heading('Type', text='Type')
        self.content_tree.heading('Count', text='Count')
        self.content_tree.heading('Details', text='Details')
        
        self.content_tree.column('#0', width=200)
        self.content_tree.column('Type', width=100)
        self.content_tree.column('Count', width=80)
        self.content_tree.column('Details', width=300)
        
        self.content_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text area for detailed content
        self.content_text = scrolledtext.ScrolledText(
            self.content_frame, height=8, wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
    def create_links_tab(self):
        """Create links analysis tab"""
        self.links_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.links_frame, text="🔗 Links")
        
        # Links summary frame
        links_summary_frame = ttk.Frame(self.links_frame)
        links_summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.links_summary_label = ttk.Label(links_summary_frame, text="", font=('Arial', 10, 'bold'))
        self.links_summary_label.pack()
        
        # Links treeview
        link_columns = ('Text', 'URL', 'Type', 'Target', 'Title')
        self.links_tree = ttk.Treeview(self.links_frame, columns=link_columns, show='headings', height=18)
        
        for col in link_columns:
            self.links_tree.heading(col, text=col)
            self.links_tree.column(col, width=150 if col != 'URL' else 300)
        
        # Scrollbars for links tree
        links_scrollbar_y = ttk.Scrollbar(self.links_frame, orient=tk.VERTICAL, command=self.links_tree.yview)
        links_scrollbar_x = ttk.Scrollbar(self.links_frame, orient=tk.HORIZONTAL, command=self.links_tree.xview)
        self.links_tree.configure(yscrollcommand=links_scrollbar_y.set, xscrollcommand=links_scrollbar_x.set)
        
        self.links_tree.pack(fill=tk.BOTH, expand=True)
        links_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        links_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_images_tab(self):
        """Create images analysis tab"""
        self.images_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.images_frame, text="🖼️ Images")
        
        # Images summary
        images_summary_frame = ttk.Frame(self.images_frame)
        images_summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.images_summary_label = ttk.Label(images_summary_frame, text="", font=('Arial', 10, 'bold'))
        self.images_summary_label.pack()
        
        # Images treeview
        image_columns = ('Alt Text', 'Source URL', 'Title', 'Dimensions', 'Loading')
        self.images_tree = ttk.Treeview(self.images_frame, columns=image_columns, show='headings', height=18)
        
        for col in image_columns:
            self.images_tree.heading(col, text=col)
            self.images_tree.column(col, width=120 if col != 'Source URL' else 300)
        
        # Scrollbars for images tree
        images_scrollbar_y = ttk.Scrollbar(self.images_frame, orient=tk.VERTICAL, command=self.images_tree.yview)
        images_scrollbar_x = ttk.Scrollbar(self.images_frame, orient=tk.HORIZONTAL, command=self.images_tree.xview)
        self.images_tree.configure(yscrollcommand=images_scrollbar_y.set, xscrollcommand=images_scrollbar_x.set)
        
        self.images_tree.pack(fill=tk.BOTH, expand=True)
        images_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        images_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_tables_tab(self):
        """Create tables analysis tab"""
        self.tables_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tables_frame, text="📊 Tables")
        
        self.tables_text = scrolledtext.ScrolledText(
            self.tables_frame, height=20, width=80, wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.tables_text.pack(fill=tk.BOTH, expand=True)
        
    def create_structured_data_tab(self):
        """Create structured data tab"""
        self.structured_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.structured_frame, text="🏗️ Structured Data")
        
        self.structured_text = scrolledtext.ScrolledText(
            self.structured_frame, height=20, width=80, wrap=tk.WORD,
            font=('Courier', 10)
        )
        self.structured_text.pack(fill=tk.BOTH, expand=True)
        
    def create_raw_data_tab(self):
        """Create raw data tab"""
        self.raw_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.raw_frame, text="🔧 Raw Data")
        
        self.raw_text = scrolledtext.ScrolledText(
            self.raw_frame, height=20, width=80, wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.raw_text.pack(fill=tk.BOTH, expand=True)
        
    def create_download_section(self):
        """Create individual file download section"""
        download_frame = ttk.LabelFrame(self.main_frame, text="💾 Download Individual Files", padding="15")
        download_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        download_frame.columnconfigure(0, weight=1)
        
        # Available files label
        self.available_files_label = ttk.Label(download_frame, text="No files available", 
                                              font=('Arial', 10), foreground=self.colors['warning'])
        self.available_files_label.grid(row=0, column=0, pady=(0, 10))
        
        # Responsive scrollable download buttons frame (horizontal and vertical)
        canvas = tk.Canvas(download_frame, height=100)
        h_scroll = ttk.Scrollbar(download_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scroll = ttk.Scrollbar(download_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.download_buttons_frame = ttk.Frame(canvas)
        self.download_buttons_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.download_buttons_frame, anchor="nw")
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        h_scroll.grid(row=2, column=0, sticky=(tk.W, tk.E))
        v_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        download_frame.grid_columnconfigure(0, weight=1)
        download_frame.grid_rowconfigure(1, weight=1)
        
        # Bulk download option
        bulk_frame = ttk.Frame(download_frame)
        bulk_frame.grid(row=2, column=0, pady=(15, 0))
        
        self.download_all_button = ttk.Button(bulk_frame, text="📦 Download All Files", 
                                            command=self.download_all_files,
                                            state=tk.DISABLED,
                                            style='Success.TButton')
        self.download_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_folder_button = ttk.Button(bulk_frame, text="📁 Select Download Folder", 
                                             command=self.select_download_folder)
        self.select_folder_button.pack(side=tk.LEFT)
        
        # Download folder label
        self.download_folder_label = ttk.Label(bulk_frame, text="No folder selected", 
                                             font=('Arial', 9), foreground=self.colors['info'])
        self.download_folder_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.download_folder = None
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Label(self.main_frame, text="Ready to scrape websites...", 
                                   relief=tk.SUNKEN, font=('Arial', 9))
        self.status_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
    def validate_url(self, event=None):
        """Validate URL format"""
        url = self.url_entry.get().strip()
        if not url or url == "https://":
            self.url_status_label.config(text="", foreground=self.colors['fg'])
            return
            
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            if parsed.netloc:
                self.url_status_label.config(text="✅ Valid URL format", 
                                           foreground=self.colors['success'])
            else:
                self.url_status_label.config(text="⚠️ Invalid URL format", 
                                           foreground=self.colors['error'])
        except:
            self.url_status_label.config(text="⚠️ Invalid URL format", 
                                       foreground=self.colors['error'])
    
    def set_url(self, url):
        """Set URL in entry field"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.validate_url()
        
    def start_scraping(self):
        """Start the enhanced scraping process"""
        url = self.url_entry.get().strip()
        
        if not url or url == "https://":
            messagebox.showerror("Error", "Please enter a valid URL to scrape")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Disable buttons during scraping
        self.scrape_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        self.download_all_button.config(state=tk.DISABLED)
        
        # Clear previous results
        self.clear_results()
        
        # Start scraping in separate thread
        self.scraping_start_time = datetime.now()
        thread = threading.Thread(target=self.scrape_website, args=(url,))
        thread.daemon = True
        thread.start()
        
    def scrape_website(self, url):
        """Scrape website using enhanced Lambda function"""
        try:
            self.update_progress(10, "🔗 Connecting to enhanced scraper...")
            
            # Prepare request
            payload = {'url': url}
            
            self.update_progress(30, "📤 Sending scraping request...")
            
            # Make request to Lambda function
            response = requests.post(
                self.lambda_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120  # Increased timeout for comprehensive scraping
            )
            
            self.update_progress(70, "⚙️ Processing comprehensive data...")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    # Store all data
                    self.scraped_data = data.get('data', {})
                    self.csv_files = data.get('csv_files', {})
                    self.full_data = data.get('full_data', {})
                    
                    # Display results in GUI
                    self.root.after(0, self.display_comprehensive_results)
                    
                    # Enable buttons
                    self.root.after(0, lambda: self.analyze_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.download_all_button.config(state=tk.NORMAL))
                    
                    # Update progress
                    elapsed_time = datetime.now() - self.scraping_start_time
                    self.update_progress(100, f"✅ Scraping completed in {elapsed_time.seconds}s!")
                    
                else:
                    error_msg = data.get('error', 'Unknown error occurred')
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Scraping failed: {error_msg}"))
                    self.update_progress(0, "❌ Scraping failed")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Server error: {response.status_code}\n{response.text}"))
                self.update_progress(0, "❌ Server error")
                
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: messagebox.showerror("Error", "Request timed out. The website might be slow to respond."))
            self.update_progress(0, "⏱️ Request timeout")
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Network error: {str(e)}"))
            self.update_progress(0, "🌐 Network error")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Unexpected error: {str(e)}"))
            self.update_progress(0, "❌ Unexpected error")
        finally:
            self.root.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))
            
    def display_comprehensive_results(self):
        """Display comprehensive scraping results"""
        if not self.scraped_data:
            return
            
        # Display summary
        self.display_summary()
        
        # Display SEO analysis
        self.display_seo_analysis()
        
        # Display content analysis
        self.display_content_analysis()
        
        # Display links
        self.display_links_analysis()
        
        # Display images
        self.display_images_analysis()
        
        # Display tables
        self.display_tables_analysis()
        
        # Display structured data
        self.display_structured_data()
        
        # Display raw data
        self.display_raw_data()
        
        # Update download section
        self.update_download_section()
        
    def display_summary(self):
        """Display website summary"""
        data = self.scraped_data
        seo_summary = data.get('seo_summary', {})
        
        summary = f"""🌐 WEBSITE ANALYSIS SUMMARY
{'='*60}

📊 BASIC INFORMATION:
URL: {data.get('url', 'N/A')}
Title: {data.get('title', 'N/A')}
Description: {data.get('description', 'N/A')[:200]}{'...' if len(data.get('description', '')) > 200 else ''}

📈 CONTENT STATISTICS:
• Word Count: {data.get('word_count', 0):,} words
• Page Size: {data.get('page_size_bytes', 0):,} bytes ({data.get('page_size_bytes', 0)/1024:.1f} KB)
• Total Headings: {data.get('total_headings', 0)}
• Total Links: {data.get('total_links', 0)}
• Total Images: {data.get('total_images', 0)}
• Total Tables: {data.get('total_tables', 0)}

📋 HEADING BREAKDOWN:
"""
        
        heading_hierarchy = data.get('heading_hierarchy', {})
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            count = heading_hierarchy.get(level, 0)
            if count > 0:
                summary += f"• {level.upper()}: {count}\n"
        
        summary += f"""
🔗 LINK ANALYSIS:
• Internal Links: {seo_summary.get('internal_links', 0)}
• External Links: {seo_summary.get('external_links', 0)}

🖼️ IMAGE ANALYSIS:
• Images without Alt Text: {seo_summary.get('images_without_alt', 0)}

📄 SEO METRICS:
• Title Length: {seo_summary.get('title_length', 0)} characters
• Description Length: {seo_summary.get('description_length', 0)} characters

📅 SCRAPED: {data.get('scraped_at', 'N/A')}

🗂️ AVAILABLE DATA FILES: {len(self.csv_files)} files ready for download
"""
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
        
    def display_seo_analysis(self):
        """Display SEO analysis"""
        if not self.full_data or 'seo_data' not in self.full_data:
            return
            
        seo_data = self.full_data['seo_data']
        
        seo_analysis = f"""🔍 SEO ANALYSIS REPORT
{'='*50}

📝 META INFORMATION:
Title Tag: {seo_data.get('title_tag', 'N/A')}
Meta Description: {seo_data.get('meta_description', 'N/A')}
Meta Keywords: {seo_data.get('meta_keywords', 'N/A') or 'Not specified'}
Canonical URL: {seo_data.get('canonical_url', 'Not specified')}
Robots: {seo_data.get('robots', 'Not specified')}
Language: {seo_data.get('lang', 'Not specified')}

📊 HEADING STRUCTURE:
"""
        
        heading_structure = seo_data.get('heading_structure', {})
        for level, count in heading_structure.items():
            if count > 0:
                seo_analysis += f"• {level.upper()}: {count}\n"
        
        seo_analysis += f"""
🔗 LINK METRICS:
• Internal Links: {seo_data.get('internal_links', 0)}
• External Links: {seo_data.get('external_links', 0)}
• Total Links: {seo_data.get('internal_links', 0) + seo_data.get('external_links', 0)}

🖼️ IMAGE SEO:
• Images without Alt Text: {seo_data.get('images_without_alt', 0)}

⚡ PERFORMANCE HINTS:
• Preload Resources: {seo_data.get('page_load_hints', {}).get('preload', 0)}
• Prefetch Resources: {seo_data.get('page_load_hints', {}).get('prefetch', 0)}

🌐 INTERNATIONALIZATION:
"""
        
        hreflang = seo_data.get('hreflang', [])
        if hreflang:
            seo_analysis += f"• Hreflang Links: {len(hreflang)}\n"
            for hl in hreflang[:5]:  # Show first 5
                seo_analysis += f"  - {hl.get('hreflang', 'N/A')}: {hl.get('href', 'N/A')}\n"
        else:
            seo_analysis += "• No hreflang tags found\n"
        
        # SEO recommendations
        seo_analysis += f"""
🎯 SEO RECOMMENDATIONS:
"""
        
        # Title analysis
        title_length = len(seo_data.get('title_tag', ''))
        if title_length == 0:
            seo_analysis += "❌ Missing title tag\n"
        elif title_length < 30:
            seo_analysis += "⚠️ Title tag too short (< 30 characters)\n"
        elif title_length > 60:
            seo_analysis += "⚠️ Title tag too long (> 60 characters)\n"
        else:
            seo_analysis += "✅ Title tag length is optimal\n"
        
        # Description analysis
        desc_length = len(seo_data.get('meta_description', ''))
        if desc_length == 0:
            seo_analysis += "❌ Missing meta description\n"
        elif desc_length < 120:
            seo_analysis += "⚠️ Meta description too short (< 120 characters)\n"
        elif desc_length > 160:
            seo_analysis += "⚠️ Meta description too long (> 160 characters)\n"
        else:
            seo_analysis += "✅ Meta description length is optimal\n"
        
        # H1 analysis
        h1_count = heading_structure.get('h1', 0)
        if h1_count == 0:
            seo_analysis += "❌ No H1 tag found\n"
        elif h1_count > 1:
            seo_analysis += "⚠️ Multiple H1 tags found (not recommended)\n"
        else:
            seo_analysis += "✅ Single H1 tag found\n"
        
        # Image alt text analysis
        images_without_alt = seo_data.get('images_without_alt', 0)
        if images_without_alt > 0:
            seo_analysis += f"⚠️ {images_without_alt} images missing alt text\n"
        else:
            seo_analysis += "✅ All images have alt text\n"
        
        self.seo_text.delete(1.0, tk.END)
        self.seo_text.insert(1.0, seo_analysis)
        
    def display_content_analysis(self):
        """Display content structure analysis"""
        if not self.full_data:
            return
            
        # Clear previous content
        for item in self.content_tree.get_children():
            self.content_tree.delete(item)
        
        # Add heading structure
        headings = self.full_data.get('headings', [])
        if headings:
            heading_node = self.content_tree.insert('', 'end', text='Headings', 
                                                   values=('Structure', len(headings), 'Page heading hierarchy'))
            
            current_level = {}
            for heading in headings[:20]:  # Show first 20 headings
                level = heading.get('level', 'h1')
                text = heading.get('text', '')[:50] + ('...' if len(heading.get('text', '')) > 50 else '')
                
                self.content_tree.insert(heading_node, 'end', text=f"{level.upper()}: {text}",
                                       values=(level, '', heading.get('id', 'No ID')))
        
        # Add content data
        content_data = self.full_data.get('content_data', {})
        
        # Navigation
        navigation = content_data.get('navigation', [])
        if navigation:
            nav_node = self.content_tree.insert('', 'end', text='Navigation', 
                                              values=('Structure', len(navigation), 'Site navigation elements'))
            for i, nav_items in enumerate(navigation[:5]):
                nav_text = f"Nav Menu {i+1} ({len(nav_items)} items)"
                self.content_tree.insert(nav_node, 'end', text=nav_text,
                                       values=('Navigation', len(nav_items), 'Menu items'))
        
        # Lists
        lists = content_data.get('lists', [])
        if lists:
            lists_node = self.content_tree.insert('', 'end', text='Lists', 
                                                 values=('Content', len(lists), 'Structured list content'))
            for i, list_item in enumerate(lists[:10]):
                list_text = f"{list_item.get('type', 'ul').upper()} List {i+1}"
                item_count = len(list_item.get('items', []))
                self.content_tree.insert(lists_node, 'end', text=list_text,
                                       values=(list_item.get('type', 'ul'), item_count, f'{item_count} items'))
        
        # Forms
        forms = self.full_data.get('structured_data', {}).get('forms', [])
        if forms:
            forms_node = self.content_tree.insert('', 'end', text='Forms', 
                                                 values=('Interactive', len(forms), 'Web forms'))
            for i, form in enumerate(forms):
                form_text = f"Form {i+1} ({form.get('method', 'GET')})"
                input_count = len(form.get('inputs', []))
                self.content_tree.insert(forms_node, 'end', text=form_text,
                                       values=(form.get('method', 'GET'), input_count, f'{input_count} inputs'))
        
        # Media
        media_list = self.full_data.get('structured_data', {}).get('media', [])
        if media_list:
            media_node = self.content_tree.insert('', 'end', text='Media Elements', 
                                                 values=('Media', len(media_list), 'Video, audio, iframe elements'))
        
        # Display detailed content in text area
        content_details = f"""📝 DETAILED CONTENT ANALYSIS
{'='*40}

💬 TEXT CONTENT SAMPLE:
{self.full_data.get('text_content', 'No content available')[:1000]}
{'...' if len(self.full_data.get('text_content', '')) > 1000 else ''}

📊 CONTENT STATISTICS:
• Total Characters: {len(self.full_data.get('text_content', ''))}
• Estimated Reading Time: {len(self.full_data.get('text_content', '').split()) // 250} minutes
• Word Count: {len(self.full_data.get('text_content', '').split())} words

🔍 CODE BLOCKS FOUND:
"""
        
        code_blocks = content_data.get('code_blocks', [])
        if code_blocks:
            for i, code in enumerate(code_blocks[:5]):
                content_details += f"• Code Block {i+1}: {code.get('tag', 'unknown')} "
                content_details += f"({code.get('language', 'no language specified')})\n"
        else:
            content_details += "• No code blocks found\n"
        
        content_details += f"""
💬 QUOTES FOUND: {len(content_data.get('quotes', []))}
"""
        
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, content_details)
        
    def display_links_analysis(self):
        """Display links analysis"""
        if not self.full_data or 'links' not in self.full_data:
            return
            
        links = self.full_data['links']
        
        # Clear previous links
        for item in self.links_tree.get_children():
            self.links_tree.delete(item)
        
        # Update summary
        internal_count = sum(1 for link in links if not link.get('is_external', False))
        external_count = sum(1 for link in links if link.get('is_external', False))
        
        self.links_summary_label.config(
            text=f"Found {len(links)} total links: {internal_count} internal, {external_count} external"
        )
        
        # Populate links tree
        for i, link in enumerate(links[:200]):  # Limit to first 200 links
            text = link.get('text', 'No text')[:50] + ('...' if len(link.get('text', '')) > 50 else '')
            url = link.get('url', '')
            link_type = 'External' if link.get('is_external', False) else 'Internal'
            target = link.get('target', '_self')
            title = link.get('title', '')[:30] + ('...' if len(link.get('title', '')) > 30 else '')
            
            self.links_tree.insert('', 'end', values=(text, url, link_type, target, title))
    
    def display_images_analysis(self):
        """Display images analysis"""
        if not self.full_data or 'images' not in self.full_data:
            return
            
        images = self.full_data['images']
        
        # Clear previous images
        for item in self.images_tree.get_children():
            self.images_tree.delete(item)
        
        # Update summary
        images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
        images_without_alt = len(images) - images_with_alt
        
        self.images_summary_label.config(
            text=f"Found {len(images)} images: {images_with_alt} with alt text, {images_without_alt} without"
        )
        
        # Populate images tree
        for img in images[:100]:  # Limit to first 100 images
            alt_text = img.get('alt', 'No alt text')[:40] + ('...' if len(img.get('alt', '')) > 40 else '')
            src = img.get('src', '')
            title = img.get('title', '')[:30] + ('...' if len(img.get('title', '')) > 30 else '')
            
            dimensions = ''
            if img.get('width') or img.get('height'):
                dimensions = f"{img.get('width', '?')} x {img.get('height', '?')}"
            
            loading = img.get('loading', 'eager')
            
            self.images_tree.insert('', 'end', values=(alt_text, src, title, dimensions, loading))
    
    def display_tables_analysis(self):
        """Display tables analysis"""
        if not self.full_data:
            return
            
        tables = self.full_data.get('tables', [])
        table_summaries = self.full_data.get('table_summaries', [])
        
        tables_info = f"""📊 TABLES ANALYSIS
{'='*40}

📈 SUMMARY:
• Total Tables Found: {len(tables)}

"""
        
        if table_summaries:
            for i, summary in enumerate(table_summaries):
                tables_info += f"""
🔍 TABLE {summary.get('table_id', i+1)}:
• Rows: {summary.get('rows', 0)}
• Columns: {summary.get('columns', 0)}
• Has Headers: {'Yes' if summary.get('has_headers', False) else 'No'}
• Caption: {summary.get('caption', 'None')}
• Headers: {', '.join(summary.get('headers', []))}

"""
                
                # Show sample data from table
                if i < len(tables) and tables[i]:
                    tables_info += "📋 SAMPLE DATA (First 3 rows):\n"
                    sample_rows = tables[i][:3]
                    for row_idx, row in enumerate(sample_rows):
                        tables_info += f"Row {row_idx + 1}: {str(row)[:100]}...\n"
                    tables_info += "\n"
        else:
            tables_info += "No tables found on this page.\n"
        
        self.tables_text.delete(1.0, tk.END)
        self.tables_text.insert(1.0, tables_info)
    
    def display_structured_data(self):
        """Display structured data analysis"""
        if not self.full_data or 'structured_data' not in self.full_data:
            return
            
        structured = self.full_data['structured_data']
        
        structured_info = f"""🏗️ STRUCTURED DATA ANALYSIS
{'='*50}

📋 JSON-LD STRUCTURED DATA:
• Found {len(structured.get('json_ld', []))} JSON-LD blocks
"""
        
        json_ld = structured.get('json_ld', [])
        for i, ld in enumerate(json_ld[:3]):  # Show first 3
            structured_info += f"\n📄 JSON-LD Block {i+1}:\n"
            structured_info += json.dumps(ld, indent=2, ensure_ascii=False)[:500] + "...\n"
        
        structured_info += f"""
🏷️ MICRODATA:
• Found {len(structured.get('microdata', []))} microdata items
"""
        
        microdata = structured.get('microdata', [])
        for i, md in enumerate(microdata[:5]):
            structured_info += f"\n📋 Microdata Item {i+1}:\n"
            structured_info += f"  Type: {md.get('itemtype', 'N/A')}\n"
            structured_info += f"  Properties: {len(md.get('properties', {}))}\n"
            for prop, value in list(md.get('properties', {}).items())[:3]:
                structured_info += f"    {prop}: {str(value)[:50]}...\n"
        
        structured_info += f"""
🏷️ META TAGS:
• Total Meta Tags: {len(structured.get('meta_tags', []))}
"""
        
        # Show important meta tags
        meta_tags = structured.get('meta_tags', [])
        important_meta = ['viewport', 'charset', 'author', 'generator', 'theme-color']
        for meta in meta_tags:
            if any(imp in meta.get('name', '').lower() for imp in important_meta):
                structured_info += f"  {meta.get('name', 'N/A')}: {meta.get('content', 'N/A')[:50]}...\n"
        
        structured_info += f"""
📱 SOCIAL MEDIA METADATA:
"""
        
        social_media = structured.get('social_media', {})
        for key, value in social_media.items():
            if value:
                structured_info += f"  {key}: {value[:60]}{'...' if len(value) > 60 else ''}\n"
        
        structured_info += f"""
📞 CONTACT INFORMATION:
• Emails Found: {len(structured.get('contact_info', {}).get('emails', []))}
• Phone Numbers Found: {len(structured.get('contact_info', {}).get('phones', []))}
"""
        
        # Show first few emails and phones
        emails = structured.get('contact_info', {}).get('emails', [])[:5]
        phones = structured.get('contact_info', {}).get('phones', [])[:5]
        
        if emails:
            structured_info += "  Emails: " + ", ".join(emails) + "\n"
        if phones:
            structured_info += "  Phones: " + ", ".join(phones) + "\n"
        
        self.structured_text.delete(1.0, tk.END)
        self.structured_text.insert(1.0, structured_info)
    
    def display_raw_data(self):
        """Display raw JSON data"""
        if not self.full_data:
            return
            
        # Display formatted JSON data
        try:
            formatted_data = json.dumps(self.full_data, indent=2, ensure_ascii=False)
            # Limit the size for display
            if len(formatted_data) > 10000:
                formatted_data = formatted_data[:10000] + "\n\n... (Data truncated for display. Full data available in downloads)"
            
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(1.0, formatted_data)
        except Exception as e:
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(1.0, f"Error displaying raw data: {str(e)}")
    
    def update_download_section(self):
        """Update the download section with available files"""
        if not self.csv_files:
            return
            
        # Clear existing buttons
        for widget in self.download_buttons_frame.winfo_children():
            widget.destroy()
        
        # Update available files label
        file_count = len(self.csv_files)
        self.available_files_label.config(
            text=f"📁 {file_count} data files available for download",
            foreground=self.colors['success']
        )
        
        # Create download buttons for each file type
        file_descriptions = {
            'main_summary': '📊 Main Summary',
            'headings': '📝 All Headings', 
            'links': '🔗 All Links',
            'images': '🖼️ All Images',
            'seo_analysis': '🔍 SEO Analysis',
            'meta_tags': '🏷️ Meta Tags',
            'social_media': '📱 Social Media',
            'contact_info': '📞 Contact Info',
            'forms_summary': '📋 Forms Data',
            'lists_summary': '📑 Lists Data',
            'full_text_content': '📄 Full Text Content'
        }
        
        # Create buttons in a grid layout
        row = 0
        col = 0
        max_cols = 3
        
        for file_key, csv_content in self.csv_files.items():
            if csv_content:  # Only create button if content exists
                display_name = file_descriptions.get(file_key, file_key.replace('_', ' ').title())
                
                # Handle table files
                if file_key.startswith('table_'):
                    display_name = f"📊 {file_key.replace('_', ' ').title()}"
                
                btn = ttk.Button(
                    self.download_buttons_frame,
                    text=display_name,
                    command=lambda key=file_key: self.download_individual_file(key),
                    width=20
                )
                btn.grid(row=row, column=col, padx=5, pady=3, sticky=tk.W)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
    
    def download_individual_file(self, file_key):
        """Download a specific CSV file"""
        if file_key not in self.csv_files or not self.csv_files[file_key]:
            messagebox.showerror("Error", f"File {file_key} not available")
            return
        
        # Ask user for save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{file_key}_{timestamp}.csv"
        
        filename = filedialog.asksaveasfilename(
            title=f"Save {file_key} data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.csv_files[file_key])
                
                messagebox.showinfo("Success", f"File saved successfully:\n{filename}")
                self.update_status(f"✅ Downloaded {file_key}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
    
    def select_download_folder(self):
        """Select folder for bulk downloads"""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder
            folder_name = os.path.basename(folder) or folder
            self.download_folder_label.config(
                text=f"📁 {folder_name}",
                foreground=self.colors['success']
            )
    
    def download_all_files(self):
        """Download all available CSV files"""
        if not self.csv_files:
            messagebox.showerror("Error", "No files available to download")
            return
        
        if not self.download_folder:
            messagebox.showwarning("Warning", "Please select a download folder first")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_files = []
            
            for file_key, csv_content in self.csv_files.items():
                if csv_content:
                    filename = f"{file_key}_{timestamp}.csv"
                    filepath = os.path.join(self.download_folder, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    saved_files.append(filename)
            
            messagebox.showinfo(
                "Success", 
                f"Successfully downloaded {len(saved_files)} files to:\n{self.download_folder}\n\n" +
                f"Files saved:\n" + "\n".join(saved_files[:10]) + 
                (f"\n... and {len(saved_files) - 10} more" if len(saved_files) > 10 else "")
            )
            
            self.update_status(f"✅ Downloaded all {len(saved_files)} files")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download files:\n{str(e)}")
    
    def analyze_results(self):
        """Open detailed analysis window"""
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to analyze. Please scrape a website first.")
            return
        
        # Switch to summary tab and show detailed analysis
        self.notebook.select(0)  # Select summary tab
        
        # Show analysis dialog
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("📊 Detailed Analysis")
        analysis_window.geometry("600x500")
        analysis_window.transient(self.root)
        analysis_window.grab_set()
        
        # Analysis content
        analysis_text = scrolledtext.ScrolledText(analysis_window, wrap=tk.WORD, font=('Courier', 10))
        analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate detailed analysis
        detailed_analysis = self.generate_detailed_analysis()
        analysis_text.insert(1.0, detailed_analysis)
        
        # Close button
        ttk.Button(analysis_window, text="Close", command=analysis_window.destroy).pack(pady=10)
    
    def generate_detailed_analysis(self):
        """Generate detailed website analysis"""
        data = self.scraped_data
        seo_summary = data.get('seo_summary', {})
        
        analysis = f"""🔍 COMPREHENSIVE WEBSITE ANALYSIS REPORT
{'='*60}

🌐 WEBSITE OVERVIEW:
URL: {data.get('url', 'N/A')}
Title: {data.get('title', 'N/A')}
Page Size: {data.get('page_size_bytes', 0):,} bytes

📊 CONTENT QUALITY SCORE:
"""
        
        # Calculate quality score
        score = 0
        max_score = 100
        
        # Title score (10 points)
        title_length = seo_summary.get('title_length', 0)
        if 30 <= title_length <= 60:
            score += 10
            analysis += "✅ Title length optimal (10/10)\n"
        elif title_length > 0:
            score += 5
            analysis += "⚠️ Title length suboptimal (5/10)\n"
        else:
            analysis += "❌ Missing title (0/10)\n"
        
        # Description score (10 points)
        desc_length = seo_summary.get('description_length', 0)
        if 120 <= desc_length <= 160:
            score += 10
            analysis += "✅ Description length optimal (10/10)\n"
        elif desc_length > 0:
            score += 5
            analysis += "⚠️ Description length suboptimal (5/10)\n"
        else:
            analysis += "❌ Missing description (0/10)\n"
        
        # Heading structure score (20 points)
        heading_hierarchy = data.get('heading_hierarchy', {})
        h1_count = heading_hierarchy.get('h1', 0)
        if h1_count == 1:
            score += 10
            analysis += "✅ Single H1 tag (10/10)\n"
        elif h1_count > 1:
            score += 5
            analysis += "⚠️ Multiple H1 tags (5/10)\n"
        else:
            analysis += "❌ No H1 tag (0/10)\n"
        
        if heading_hierarchy.get('h2', 0) > 0:
            score += 10
            analysis += "✅ H2 tags present (10/10)\n"
        else:
            analysis += "❌ No H2 tags (0/10)\n"
        
        # Image optimization score (20 points)
        total_images = data.get('total_images', 0)
        images_without_alt = seo_summary.get('images_without_alt', 0)
        if total_images > 0:
            alt_ratio = (total_images - images_without_alt) / total_images
            image_score = int(20 * alt_ratio)
            score += image_score
            analysis += f"📊 Image alt text coverage: {alt_ratio:.1%} ({image_score}/20)\n"
        else:
            analysis += "ℹ️ No images found (N/A)\n"
        
        # Link structure score (20 points)
        internal_links = seo_summary.get('internal_links', 0)
        external_links = seo_summary.get('external_links', 0)
        
        if internal_links > 0:
            score += 10
            analysis += "✅ Internal links present (10/10)\n"
        else:
            analysis += "❌ No internal links (0/10)\n"
        
        if 0 < external_links <= 10:
            score += 10
            analysis += "✅ Balanced external links (10/10)\n"
        elif external_links > 10:
            score += 5
            analysis += "⚠️ Many external links (5/10)\n"
        else:
            analysis += "❌ No external links (0/10)\n"
        
        # Content length score (20 points)
        word_count = data.get('word_count', 0)
        if word_count >= 300:
            score += 20
            analysis += f"✅ Sufficient content: {word_count:,} words (20/20)\n"
        elif word_count >= 100:
            score += 10
            analysis += f"⚠️ Limited content: {word_count:,} words (10/20)\n"
        else:
            analysis += f"❌ Insufficient content: {word_count:,} words (0/20)\n"
        
        # Final score
        percentage = (score / max_score) * 100
        analysis += f"""
🏆 OVERALL QUALITY SCORE: {score}/{max_score} ({percentage:.1f}%)

📋 SCORE INTERPRETATION:
"""
        if percentage >= 90:
            analysis += "🟢 Excellent - Your page is well-optimized!\n"
        elif percentage >= 70:
            analysis += "🟡 Good - Minor improvements recommended\n"
        elif percentage >= 50:
            analysis += "🟠 Fair - Several areas need attention\n"
        else:
            analysis += "🔴 Poor - Significant optimization needed\n"
        
        analysis += f"""
💡 KEY RECOMMENDATIONS:
"""
        
        # Add specific recommendations
        recommendations = []
        
        if title_length == 0:
            recommendations.append("• Add a descriptive title tag")
        elif not (30 <= title_length <= 60):
            recommendations.append("• Optimize title tag length (30-60 characters)")
        
        if desc_length == 0:
            recommendations.append("• Add a meta description")
        elif not (120 <= desc_length <= 160):
            recommendations.append("• Optimize meta description length (120-160 characters)")
        
        if h1_count == 0:
            recommendations.append("• Add an H1 heading")
        elif h1_count > 1:
            recommendations.append("• Use only one H1 tag per page")
        
        if heading_hierarchy.get('h2', 0) == 0:
            recommendations.append("• Add H2 headings for better structure")
        
        if images_without_alt > 0:
            recommendations.append(f"• Add alt text to {images_without_alt} images")
        
        if internal_links == 0:
            recommendations.append("• Add internal links to improve navigation")
        
        if word_count < 300:
            recommendations.append("• Increase content length for better SEO")
        
        if not recommendations:
            recommendations.append("• Great job! Your page is well-optimized.")
        
        analysis += "\n".join(recommendations)
        
        return analysis
    
    def clear_results(self):
        """Clear all result displays"""
        # Clear text widgets
        text_widgets = [
            self.summary_text, self.seo_text, self.content_text,
            self.tables_text, self.structured_text, self.raw_text
        ]
        
        for widget in text_widgets:
            widget.delete(1.0, tk.END)
        
        # Clear tree widgets
        for item in self.content_tree.get_children():
            self.content_tree.delete(item)
        for item in self.links_tree.get_children():
            self.links_tree.delete(item)
        for item in self.images_tree.get_children():
            self.images_tree.delete(item)
        
        # Clear summary labels
        self.links_summary_label.config(text="")
        self.images_summary_label.config(text="")
    
    def clear_all(self):
        """Clear all data and reset GUI"""
        # Clear URL
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "https://")
        self.url_status_label.config(text="")
        
        # Clear results
        self.clear_results()
        
        # Clear download section
        for widget in self.download_buttons_frame.winfo_children():
            widget.destroy()
        
        self.available_files_label.config(
            text="No files available",
            foreground=self.colors['warning']
        )
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="Ready to scrape...")
        self.time_label.config(text="")
        self.status_bar.config(text="Ready to scrape websites...")
        
        # Reset download folder
        self.download_folder = None
        self.download_folder_label.config(
            text="No folder selected",
            foreground=self.colors['info']
        )
        
        # Reset buttons
        self.analyze_button.config(state=tk.DISABLED)
        self.download_all_button.config(state=tk.DISABLED)
        
        # Clear data
        self.scraped_data = {}
        self.csv_files = {}
        self.full_data = {}
        
        self.update_status("🗑️ All data cleared")
        
    def update_progress(self, value, message):
        """Update progress bar and labels"""
        self.progress_var.set(value)
        self.progress_label.config(text=message)
        self.status_bar.config(text=message)
        
        # Update time estimation
        if hasattr(self, 'scraping_start_time') and value > 0 and value < 100:
            elapsed = (datetime.now() - self.scraping_start_time).total_seconds()
            if value > 10:  # Only estimate after some progress
                estimated_total = (elapsed / value) * 100
                remaining = estimated_total - elapsed
                self.time_label.config(text=f"⏱️ Estimated time remaining: {int(remaining)}s")
        elif value == 100:
            if hasattr(self, 'scraping_start_time'):
                total_time = (datetime.now() - self.scraping_start_time).total_seconds()
                self.time_label.config(text=f"✅ Completed in {int(total_time)}s")
        
        self.root.update_idletasks()
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()

def main():
    """Main function to run the enhanced GUI"""
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        root.iconbitmap('scraper_icon.ico')
    except:
        pass  # Ignore if icon not found
    
    # Initialize the enhanced GUI
    app = EnhancedWebScraperGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()