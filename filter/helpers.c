#include "helpers.h"
#include <math.h>

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    int avg, red, green, blue;

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            red = image[i][j].rgbtRed;
            green = image[i][j].rgbtGreen;
            blue = image[i][j].rgbtBlue;

            avg = round((red + green + blue) / 3.0);
            image[i][j].rgbtRed = image[i][j].rgbtBlue = image[i][j].rgbtGreen = avg;
        }
    }
    return;
}

// Convert image to sepia
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    int red, green, blue;

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            red = image[i][j].rgbtRed;
            green = image[i][j].rgbtGreen;
            blue = image[i][j].rgbtBlue;

            int red_sepia = round(0.393 * red + 0.769 * green + 0.189 * blue);
            if (red_sepia > 255)
            {
                image[i][j].rgbtRed = 255;
            }
            else
            {
                image[i][j].rgbtRed = red_sepia;
            }

            int green_sepia = round(0.349 * red + 0.686 * green + 0.168 * blue);
            if (green_sepia > 255)
            {
                image[i][j].rgbtGreen = 255;
            }
            else
            {
                image[i][j].rgbtGreen = green_sepia;
            }

            int blue_sepia = round(0.272 * red + 0.534 * green + 0.131 * blue);
            if (blue_sepia > 255)
            {
                image[i][j].rgbtBlue = 255;
            }
            else
            {
                image[i][j].rgbtBlue = blue_sepia;
            }
        }
    }
    return;
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width / 2; j++)
        {
            RGBTRIPLE tmp = image[i][j];

            image[i][j] = image[i][width - (j + 1)];
            image[i][width - (j + 1)] = tmp;
        }
    }
    return;
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    RGBTRIPLE tmp[height][width];
    int red = 0;
    int green = 0;
    int blue = 0;
    int counter = 0;

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < height; j++)
        {
            for (int x = -1; x < 2; x++)
            {
                for (int y = -1; y < 2; y++)
                {
                    int cx = i + x;
                    int cy = j + y;
                    if (cx < 0 || cx > (height - 1) || cy < 0 || cy > (width - 1))
                    {
                        continue;
                    }

                    red += image[cx][cy].rgbtRed;
                    green += image[cx][cy].rgbtGreen;
                    blue += image[cx][cy].rgbtBlue;

                    counter++;
                }

                tmp[i][j].rgbtRed = round(red / (float)counter);
                tmp[i][j].rgbtGreen = round(green / (float)counter);
                tmp[i][j].rgbtBlue = round(blue / (float)counter);
            }
        }
    }

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width / 2; j++)
        {
            image[i][j].rgbtRed = tmp[i][j].rgbtRed;
            image[i][j].rgbtGreen = tmp[i][j].rgbtGreen;
            image[i][j].rgbtBlue = tmp[i][j].rgbtBlue;
        }
    }
    return;
}
