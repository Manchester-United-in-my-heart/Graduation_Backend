// Use import statements for ES modules
import { EPub } from '@lesjoursfr/html-to-epub';
import fs from 'fs';

fs.readFile('html_content.json', 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading file: ', err);
    return;
  }

  const content = JSON.parse(data);

  // Create the EPub instance with content
  const epub = new EPub(
    {
      title: 'My First Ebook',
      content: content.map((section) => ({
        title: section.title ? section.title : 'Untitled',
        data: section.data,
      })),
    },
    './my-first-ebook.epub'
  );

  epub
    .render()
    .then(() => {
      console.log('Ebook Generated Successfully!');
    })
    .catch((err) => {
      console.error('Failed to generate Ebook because of ', err);
    });
});

// // Create the EPub instance with content
// const epub = new EPub(
//   {
//     title: 'My First Ebook',
//     content: [
//       {
//         title: 'Chapter 1',
//         data: '<h1>This is Chapter 1</h1><p>Content of Chapter 1</p>',
//       },
//       {
//         title: 'Chapter 2',
//         data: '<h1>This is Chapter 2</h1><p>Content of Chapter 2</p>',
//       },
//     ],
//   },
//   './my-first-ebook.epub'
// );

// // Render the EPUB
// epub
//   .render()
//   .then(() => {
//     console.log('Ebook Generated Successfully!');
//   })
//   .catch((err) => {
//     console.error('Failed to generate Ebook because of ', err);
//   });
