interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  keywords: string;
  logo: string;
  navLinks: {
    name: string;
    url: string;
  }[];
}

const data: ISiteMetadataResult = {
  siteTitle: 'Workouts Map',
  siteUrl: 'https://blog.lemmo.top',
  logo: 'https://pub-6270652de33146ff80af9863a44d6003.r2.dev/2024/06/665ea189301f8.png',
  description: 'Personal site and blog',
  keywords: 'workouts, running, cycling, riding, roadtrip, hiking, swimming',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://blog.lemmo.top',
    },
    {
      name: 'About',
      url: 'https://github.com/yslemmo/workouts_page/blob/master/README-CN.md',
    },
  ],
};

export default data;
