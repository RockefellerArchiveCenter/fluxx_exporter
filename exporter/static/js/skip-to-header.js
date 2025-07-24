// Enable keyboard navigation to skip to the next section of the page when a skip link is clicked.
document.addEventListener('DOMContentLoaded', function() {
  const skipLinks = document.querySelectorAll('.toc__skip-link');
  const headings = Array.from(document.querySelectorAll('h2, h3, h4'));
  const submitBtn = document.getElementById('submit-btn');

  // For each skip link, set its target
  skipLinks.forEach(function(skipLink) {
    // Find the first heading after the skip link in document order
    const nextHeading = headings.find(
      h => h.compareDocumentPosition(skipLink) & Node.DOCUMENT_POSITION_PRECEDING
    );
    if (nextHeading) {
      // Assign a unique id to the heading if it doesn't have one
      if (!nextHeading.id) {
        nextHeading.id = 'skip-' + Math.random().toString(36).slice(2, 8);
      }
      // Set the skip link to point to the heading
      skipLink.href = '#' + nextHeading.id;
    } else if (submitBtn) {
      // If no heading is found, point to the submit button
      skipLink.href = '#' + submitBtn.id;
    }
  });
});