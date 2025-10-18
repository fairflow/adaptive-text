import plotly.graph_objects as go
import plotly.express as px

# Create a wireframe mockup using plotly
fig = go.Figure()

# Define layout dimensions
fig.update_layout(
    title="Adaptive Text Viewer Interface Wireframe",
    xaxis=dict(range=[0, 100], showgrid=False, showticklabels=False, zeroline=False),
    yaxis=dict(range=[0, 100], showgrid=False, showticklabels=False, zeroline=False),
    showlegend=False,
    plot_bgcolor='white'
)

# Left Sidebar (25% width)
fig.add_shape(type="rect", x0=0, y0=0, x1=25, y1=100, 
              line=dict(color="black", width=2), fillcolor="#f5f5f5")

# Main Content Area (75% width)  
fig.add_shape(type="rect", x0=25, y0=0, x1=100, y1=100,
              line=dict(color="black", width=2), fillcolor="#f9f9f9")

# Left Sidebar Components
fig.add_shape(type="rect", x0=2, y0=90, x1=23, y1=98, 
              line=dict(color="gray", width=1), fillcolor="#e0e0e0")
fig.add_annotation(x=12.5, y=94, text="CONTENT CONTROLS", showarrow=False, font=dict(size=10, color="black"))

fig.add_shape(type="rect", x0=2, y0=75, x1=23, y1=88, 
              line=dict(color="gray", width=1), fillcolor="white")
fig.add_annotation(x=12.5, y=81.5, text="Resolution Level<br>0-3: Summary|Condensed<br>Standard|Expanded", 
                  showarrow=False, font=dict(size=8, color="black"))

fig.add_shape(type="rect", x0=2, y0=60, x1=23, y1=73, 
              line=dict(color="gray", width=1), fillcolor="white")
fig.add_annotation(x=12.5, y=66.5, text="Formality<br>1-10: Casual to Formal", 
                  showarrow=False, font=dict(size=8, color="black"))

fig.add_shape(type="rect", x0=2, y0=45, x1=23, y1=58, 
              line=dict(color="gray", width=1), fillcolor="white")
fig.add_annotation(x=12.5, y=51.5, text="Reading Age<br>8-18 years", 
                  showarrow=False, font=dict(size=8, color="black"))

fig.add_shape(type="rect", x0=2, y0=25, x1=23, y1=43, 
              line=dict(color="gray", width=1), fillcolor="white")
fig.add_annotation(x=12.5, y=34, text="Wallet<br>Balance: 100.0 credits<br>Blocks purchased: 0", 
                  showarrow=False, font=dict(size=8, color="black"))

fig.add_shape(type="rect", x0=2, y0=15, x1=23, y1=23, 
              line=dict(color="gray", width=1), fillcolor="#d0d0d0")
fig.add_annotation(x=12.5, y=19, text="Reset Button", showarrow=False, font=dict(size=8, color="black"))

# Main Content Area Components
fig.add_shape(type="rect", x0=27, y0=90, x1=98, y1=98, 
              line=dict(color="gray", width=1), fillcolor="#e0e0e0")
fig.add_annotation(x=62.5, y=94, text="The Future of Adaptive Text Systems", 
                  showarrow=False, font=dict(size=12, color="black"))

fig.add_shape(type="rect", x0=27, y0=82, x1=98, y1=88, 
              line=dict(color="gray", width=1), fillcolor="#e0e0e0")
fig.add_annotation(x=62.5, y=85, text="Level 0: Summary | Level 1: Condensed | Level 2: Standard | Level 3: Expanded", 
                  showarrow=False, font=dict(size=9, color="black"))

# Section 1 (Locked)
fig.add_shape(type="rect", x0=27, y0=60, x1=98, y1=80, 
              line=dict(color="gray", width=1), fillcolor="#e6e6e6")
fig.add_annotation(x=30, y=76, text="🔒", showarrow=False, font=dict(size=12, color="black"))
fig.add_annotation(x=40, y=76, text="Section 1 - 0.50 cr", showarrow=False, font=dict(size=10, color="black"))
fig.add_annotation(x=62.5, y=70, text="Gray Preview Text Box", showarrow=False, font=dict(size=9, color="gray"))
fig.add_shape(type="rect", x0=60, y0=62, x1=85, y1=67, 
              line=dict(color="gray", width=1), fillcolor="#d0d0d0")
fig.add_annotation(x=72.5, y=64.5, text="Unlock for 0.50 credits", showarrow=False, font=dict(size=8, color="black"))

# Section 2 (Owned)
fig.add_shape(type="rect", x0=27, y0=35, x1=98, y1=58, 
              line=dict(color="gray", width=1), fillcolor="#e6f3e6")
fig.add_annotation(x=30, y=54, text="✓", showarrow=False, font=dict(size=12, color="green"))
fig.add_annotation(x=40, y=54, text="Section 2 - OWNED", showarrow=False, font=dict(size=10, color="black"))
fig.add_annotation(x=62.5, y=46.5, text="Full Text Content<br>Display Area", showarrow=False, font=dict(size=9, color="black"))
fig.add_shape(type="rect", x0=60, y0=37, x1=85, y1=42, 
              line=dict(color="gray", width=1), fillcolor="#c0e0c0")
fig.add_annotation(x=72.5, y=39.5, text="Download Section 2", showarrow=False, font=dict(size=8, color="black"))

# Section 3 (Locked)
fig.add_shape(type="rect", x0=27, y0=10, x1=98, y1=33, 
              line=dict(color="gray", width=1), fillcolor="#e6e6e6")
fig.add_annotation(x=30, y=29, text="🔒", showarrow=False, font=dict(size=12, color="black"))
fig.add_annotation(x=40, y=29, text="Section 3 - 2.00 cr", showarrow=False, font=dict(size=10, color="black"))
fig.add_annotation(x=62.5, y=21.5, text="Gray Preview Text Box", showarrow=False, font=dict(size=9, color="gray"))
fig.add_shape(type="rect", x0=60, y0=12, x1=85, y1=17, 
              line=dict(color="gray", width=1), fillcolor="#d0d0d0")
fig.add_annotation(x=72.5, y=14.5, text="Unlock for 2.00 credits", showarrow=False, font=dict(size=8, color="black"))

# Save the wireframe
fig.write_image("wireframe_mockup.png")
fig.write_image("wireframe_mockup.svg", format="svg")

fig.show()