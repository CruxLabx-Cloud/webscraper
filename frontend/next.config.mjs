/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,

    // Enable SWR compression
    compress: true,

    // Enable static optimization
    staticPageGenerationTimeout: 60,

    // Optimize images
    images: {
        unoptimized: true, // Since we're not using Next.js Image component
    },

    // Security headers
    headers: async() => {
        return [{
            source: '/:path*',
            headers: [{
                    key: 'X-Content-Type-Options',
                    value: 'nosniff',
                },
                {
                    key: 'X-Frame-Options',
                    value: 'DENY',
                },
                {
                    key: 'X-XSS-Protection',
                    value: '1; mode=block',
                },
                {
                    key: 'Referrer-Policy',
                    value: 'strict-origin-when-cross-origin',
                },
                {
                    key: 'Permissions-Policy',
                    value: 'geolocation=(), microphone=(), camera=()',
                },
            ],
        }, ];
    },

    // Redirect trailing slashes
    trailingSlash: false,
};

export default nextConfig;