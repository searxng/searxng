<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" version="5" encoding="UTF-8" indent="yes" />
  <xsl:template match="rss">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title><xsl:value-of select="channel/title" />RSS Feed</title>
        <meta charset="UTF-8" />
        <meta http-equiv="x-ua-compatible" content="IE=edge,chrome=1" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
	<link rel="stylesheet" href="{{ url_for('static', filename='sxng-rss.min.css') }}" type="text/css" media="screen"/>
      </head>
      <body>
        <header>
          <h2>
            <xsl:value-of select="channel/description" />
          </h2>
        </header>
	<hr />
        <main>
          <xsl:for-each select="channel/item">
            <article>
              <h3>
                <a hreflang="en" target="_blank">
                  <xsl:attribute name="href">
                    <xsl:value-of select="link" />
                  </xsl:attribute>
                  <xsl:value-of select="title" />
                </a>
              </h3>
              <time><xsl:value-of select="pubDate" /></time>
	      <p><xsl:value-of select="description" /></p>
	      <hr />
            </article>
          </xsl:for-each>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
